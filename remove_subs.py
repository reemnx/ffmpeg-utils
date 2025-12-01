import cv2
import sys
import os

def process_video(video_path, mask_path, output_path):
    # 1. בדיקת קיום קבצים
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        return
    if not os.path.exists(mask_path):
        print(f"Error: Mask file not found at {mask_path}")
        return

    # 2. טעינת הסרטון
    cap = cv2.VideoCapture(video_path)
    
    # קבלת נתוני הסרטון (רוחב, גובה, FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"Video Info: {width}x{height} @ {fps}fps, Total frames: {total_frames}")

    # 3. טעינת והכנת המסכה
    # אנו טוענים כ-Grayscale כי המסכה צריכה להיות ערוץ אחד
    mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
    mask = cv2.GaussianBlur(mask, (21, 21), 0)  # softer edges
    
    # וידוא שהמסכה בגודל הסרטון, אם לא - משנים גודל
    if mask.shape != (height, width):
        print(f"Warning: Mask size {mask.shape[::-1]} differs from video size {(width, height)}. Resizing mask...")
        mask = cv2.resize(mask, (width, height))

    # המרה לבינארי (שחור/לבן מוחלט) ליתר ביטחון
    _, mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)

    # 4. הגדרת כתיבת קובץ הפלט
    fourcc = cv2.VideoWriter_fourcc(*'mp4v') # מקודד סטנדרטי
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    print("Starting processing... (This might take a while)")

    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # --- הלב של התוכנית: Inpainting ---
        # radius=3: רדיוס הפיקסלים מסביב למסכה שנלקחים בחשבון
        # flags=cv2.INPAINT_TELEA: האלגוריתם (אפשר לנסות גם cv2.INPAINT_NS)
        inpainted_frame = cv2.inpaint(frame, mask, 3, cv2.INPAINT_TELEA)

        out.write(inpainted_frame)

        # הדפסת התקדמות כל 50 פריימים
        frame_count += 1
        if frame_count % 50 == 0:
            percent = int((frame_count / total_frames) * 100)
            print(f"Processed: {percent}% ({frame_count}/{total_frames})")

    # שחרור משאבים
    cap.release()
    out.release()
    print(f"\nDone! Saved to: {output_path}")

if __name__ == "__main__":
    # שנה את הנתיבים כאן בהתאם לקבצים שלך
    video_file = "input_video.mp4"   # שם קובץ הווידאו שלך
    mask_file = "mask_image.png"     # שם קובץ המסכה
    output_file = "clean_video.mp4"  # שם קובץ התוצאה
    
    process_video(video_file, mask_file, output_file)