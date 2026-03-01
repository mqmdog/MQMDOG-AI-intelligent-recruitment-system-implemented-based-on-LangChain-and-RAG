"""简历文件上传工具函数"""
import os
from uuid import uuid4

import aiofiles
from fastapi import UploadFile, HTTPException, status
from loguru import logger

from core.pdf import WordToPdfConverter
from settings import settings

ALLOWED_MIME_TYPES = [
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "image/jpeg",
    "image/png",
    "image/jpg",
]


async def save_resume_file(file: UploadFile) -> str:
    """校验文件类型 -> 保存文件 -> Word 转 PDF -> 返回文件路径"""
    # 1. 校验文件类型
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="该文件不支持！")

    # 2. 保存文件
    resume_dir = settings.RESUME_DIR
    file_extension = os.path.splitext(file.filename)[-1]
    unique_filename = f"{uuid4()}{file_extension}"
    file_path = os.path.join(resume_dir, unique_filename)

    async with aiofiles.open(file_path, mode="wb") as fp:
        content = await file.read(1024)
        while content:
            await fp.write(content)
            content = await file.read(1024)

    # 3. Word 文档转换为 PDF
    if file_extension in (".doc", ".docx"):
        pdf_path = file_path.replace(file_extension, ".pdf")
        converter = WordToPdfConverter(
            word_path=file_path, output_pdf_path=pdf_path)
        try:
            await converter.convert()
            file_path = pdf_path
        except Exception as e:
            logger.error(f"Word转pdf失败：{e}")
            logger.info(f"继续使用原始Word文件进行上传: {file_path}")

    return file_path
