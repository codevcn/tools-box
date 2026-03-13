import os
import json
import re
import time
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi
from google import genai
from google.genai import types
from pathlib import Path

# Tải các biến môi trường từ file .env
load_dotenv(".env")

# Lấy đường dẫn tuyệt đối của tệp hiện tại
current_file = Path(__file__).resolve()
# Lấy thư mục cha (thư mục chứa tệp này)
root_dir = current_file.parent.parent

# 1. Cấu hình Client cho Gemini theo chuẩn SDK mới (google-genai)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Lỗi: Biến môi trường GEMINI_API_KEY chưa được thiết lập.")
    exit(1)
client = genai.Client(api_key=GEMINI_API_KEY)

# Sử dụng mô hình mới nhất để tối ưu khả năng dịch thuật và xử lý JSON
GEMINI_MODEL = os.getenv("GEMINI_MODEL")
if not GEMINI_MODEL:
    print("Lỗi: Biến môi trường GEMINI_MODEL chưa được thiết lập.")
    exit(1)

TRANSLATE_CHUNK_SIZE = int(os.getenv("TRANSLATE_CHUNK_SIZE", 0))
if TRANSLATE_CHUNK_SIZE <= 0:
    print(
        "Cảnh báo: Biến môi trường TRANSLATE_CHUNK_SIZE không hợp lệ hoặc không được thiết lập."
    )
    exit(1)


def get_youtube_subtitle(video_id):
    """Tải phụ đề tiếng Anh từ YouTube."""
    try:
        print("Đang tải phụ đề gốc...")
        # LƯU Ý: YouTubeTranscriptApi trả về một danh sách các từ điển (list of dicts).
        # Do đó, ta cần sử dụng cú pháp chuẩn của thư viện là get_transcript.
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id, languages=["en"])
        return transcript
    except Exception as e:
        print(f"Lỗi khi tải phụ đề: {e}")
        return None


def format_time(seconds):
    """Chuyển đổi giây sang định dạng thời gian chuẩn của SRT."""
    td = float(seconds)
    hours = int(td // 3600)
    minutes = int((td % 3600) // 60)
    secs = int(td % 60)
    millis = int((td % 1) * 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"


def load_summary(youtube_video_link: str) -> str | None:
    """Đọc nội dung tóm tắt phim từ file, hoặc yêu cầu Gemini tóm tắt nếu chưa có."""
    summary_path = root_dir / "input" / "video_summary.md"

    # 1. Kiểm tra xem file đã tồn tại và có nội dung hay chưa
    if summary_path.exists():
        content = summary_path.read_text(encoding="utf-8").strip()
        if content:
            print("Đã tìm thấy bản tóm tắt có sẵn trong file video_summary.md.")
            return content

    if not GEMINI_MODEL:
        print("Lỗi: Biến môi trường GEMINI_MODEL chưa được thiết lập.")
        return None

    # 2. Nếu không có file hoặc file rỗng, gọi API để yêu cầu tóm tắt
    prompt = f"""
    Bạn hãy tóm tắt nội dung của video YouTube tại đường dẫn sau: {youtube_video_link}
    
    Vui lòng trả về kết quả theo đúng định dạng dưới đây:
    - Title:
    - Genre:
    - Main Characters:
    - Theme:
    - Summary (theo video timeline): (viết thành từng đoạn văn, các đoạn văn có thứ tự nối tiếp nhau dựa trên trình tự thời gian của video)
    """

    try:
        print(f"Đang gửi yêu cầu tóm tắt video {youtube_video_link} đến Gemini...")

        # Gọi API để tạo nội dung tóm tắt
        response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)

        # Kiểm tra xem API có trả về văn bản hợp lệ hay không
        summary_text = response.text
        if summary_text:
            print("Đã nhận được bản tóm tắt từ Gemini thành công.")
            return summary_text
        else:
            print("Lỗi: Nhận được phản hồi nhưng không có nội dung văn bản từ Gemini.")
            return None

    except Exception as e:
        # Bắt mọi lỗi xảy ra trong quá trình kết nối hoặc xử lý của API
        print(f"Đã xảy ra lỗi trong quá trình gọi API để tóm tắt video: {e}")
        return None


def translate_chunk(chunk_data, summary: str | None = None, max_retries: int = 3):
    """Dịch một cụm nhỏ phụ đề, không dùng lịch sử chat để tránh tràn token."""
    payload = [{"id": i, "text": item.text} for i, item in enumerate(chunk_data)]

    # Ghép bản tóm tắt trực tiếp vào ngữ cảnh của câu lệnh
    context_text = (
        f"Tóm tắt phim (dùng để tham khảo bối cảnh phim):\n{summary}\n\n"
        if summary
        else ""
    )

    translate_prompt = f"""
    Bạn là một chuyên gia dịch thuật phim ảnh. {context_text}
    Yêu cầu:
    1. Hãy dịch các dòng phụ đề sau từ tiếng Anh sang tiếng Việt.
    2. Giữ nguyên văn phong tự nhiên, sát với ngữ cảnh giao tiếp.
    3. Bạn TUYỆT ĐỐI KHÔNG thêm bất kỳ bình luận nào.
    4. Trả về đúng định dạng JSON array ban đầu, chỉ thay đổi nội dung bên trong trường "text" thành tiếng Việt.
    
    Dữ liệu cần dịch:
    {json.dumps(payload, ensure_ascii=False)}
    """
    if not GEMINI_MODEL:
        print("Lỗi: Biến môi trường GEMINI_MODEL chưa được thiết lập.")
        return None

    for attempt in range(1, max_retries + 1):
        try:
            # Gọi API dạng stateless (không lưu lịch sử) thay vì dùng chat
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=translate_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                ),
            )

            if response.text is None:
                raise ValueError("API trả về phản hồi rỗng.")
            result = json.loads(response.text)
            if len(result) != len(chunk_data):
                raise ValueError(
                    f"Số dòng trả về ({len(result)}) không khớp ({len(chunk_data)})."
                )
            return result
        except Exception as e:
            err_str = str(e)
            print(f"  Lần thử {attempt}/{max_retries} thất bại: {e}")

            # Nếu model không có free tier (limit: 0), không cần retry thêm
            if "limit: 0" in err_str:
                print(
                    "  Model không có free tier hoặc quota đã hết hoàn toàn. Vui lòng đổi model hoặc nâng cấp plan."
                )
                return None

            if attempt < max_retries:
                # Đọc thời gian chờ (retryDelay) từ phản hồi lỗi nếu có (ví dụ: 'Please retry in 56s')
                match = re.search(r"retry[\w\s]*in[\s]+(\d+)", err_str, re.IGNORECASE)
                wait = int(match.group(1)) + 5 if match else 65 * attempt
                print(f"  Chờ {wait}s trước khi thử lại...")
                time.sleep(wait)

    return None


def process_and_save_srt(original_data, filename: str, youtube_video_link: str):
    """Xử lý chia nhỏ dữ liệu, dịch và lưu thành file SRT."""
    translated_subtitles = []

    summary = load_summary(youtube_video_link)
    if summary:
        print("Đã tải bản tóm tắt phim. Sẽ dùng bản tóm tắt làm ngữ cảnh cho từng cụm.")
    else:
        print("Không có bản tóm tắt phim. Sẽ dịch mà không có ngữ cảnh phim.")

    total_lines = len(original_data)
    print(f"Tổng cộng có {total_lines} dòng phụ đề. Bắt đầu quá trình dịch...")

    for i in range(0, total_lines, TRANSLATE_CHUNK_SIZE):
        chunk = original_data[i : i + TRANSLATE_CHUNK_SIZE]
        print(
            f"Đang xử lý dòng {i + 1} đến {min(i + TRANSLATE_CHUNK_SIZE, total_lines)}..."
        )

        # Truyền trực tiếp summary vào hàm dịch
        translated_chunk = translate_chunk(chunk, summary)

        # Kiểm tra tính hợp lệ của dữ liệu trả về
        if translated_chunk:
            translated_subtitles.extend(translated_chunk)
        else:
            print(
                f"Cảnh báo: Chunk {i+1} thất bại sau {3} lần thử. Giữ nguyên tiếng Anh."
            )
            # Fallback: Nếu AI trả về lỗi, giữ nguyên bản gốc để không làm hỏng file
            fallback_chunk = [{"text": item.text} for item in chunk]
            translated_subtitles.extend(fallback_chunk)

        # Tạm nghỉ 4 giây giữa các lần gọi để đảm bảo an toàn cho gói miễn phí (tránh vượt rate limit)
        time.sleep(4)

    # Ghi dữ liệu ra file SRT
    print("Đang định dạng và lưu file SRT...")
    with open(filename, "w", encoding="utf-8") as f:
        # Sử dụng hàm zip để ráp thời gian gốc và văn bản đã dịch một cách chính xác
        for index, (orig, trans) in enumerate(zip(original_data, translated_subtitles)):
            start_time = format_time(orig.start)
            end_time = format_time(orig.start + orig.duration)
            translated_text = trans.get("text", orig.text)

            f.write(f"{index + 1}\n{start_time} --> {end_time}\n{translated_text}\n\n")

    print(f"Hoàn thành! File '{filename}' đã sẵn sàng.")


def extract_video_id(url: str) -> str:
    """Trích xuất Video ID từ nhiều định dạng đường dẫn YouTube khác nhau."""
    # Loại bỏ dấu nháy đơn/kép bao quanh URL (thường do đọc từ file config)
    url = url.strip().strip("\"'")
    parsed = urlparse(url)
    if parsed.hostname == "youtu.be":
        # Hỗ trợ: https://youtu.be/EKgy5EM-Vhw?si=xxx
        return parsed.path.lstrip("/")
    if parsed.hostname in ("www.youtube.com", "youtube.com"):
        if parsed.path == "/watch":
            # Hỗ trợ: https://www.youtube.com/watch?v=EKgy5EM-Vhw
            return parse_qs(parsed.query)["v"][0]
        if parsed.path.startswith("/embed/"):
            return parsed.path.split("/")[2]
    raise ValueError(f"Không nhận ra URL YouTube: {url}")


def load_video_link_from_input(config_path: str | None = None) -> str:
    """Đọc đường dẫn video YouTube từ file cấu hình."""
    if config_path is None:
        config_path = os.path.join(root_dir, "input", "video_config.txt")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("youtube_video_link"):
                    return line.split("=", 1)[1].strip()
        raise ValueError(f"Không tìm thấy 'youtube_video_link' trong {config_path}")
    except Exception as e:
        print(f"Lỗi khi đọc file cấu hình: {e}")
        exit(1)


# --- Thực thi chương trình ---
if __name__ == "__main__":
    youtube_video_link = load_video_link_from_input()
    video_id: str = ""
    try:
        video_id = extract_video_id(youtube_video_link)
        print(f"Đã trích xuất thành công Video ID: {video_id}")
    except ValueError as e:
        print(e)
        exit(1)

    data = get_youtube_subtitle(video_id)
    if data:
        output_dir = os.path.join(root_dir, "result")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"vietsub_{video_id}.srt")
        process_and_save_srt(
            data, filename=output_path, youtube_video_link=youtube_video_link
        )
