import zipfile
import io

def make_zip(files):
  buffer = io.BytesIO()

  with zipfile.ZipFile(buffer, "w") as zipf:
    for file in files:
      zipf.write(file, arcname=file.name)

  buffer.seek(0)
  return buffer