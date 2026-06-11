import io
import zipfile


def make_zip(files, arcnames=None):
    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, "w") as zipf:
        for i, file in enumerate(files):
            name = arcnames[i] if arcnames else file.name
            zipf.write(file, arcname=name)

    buffer.seek(0)
    return buffer
