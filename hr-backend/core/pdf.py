import asyncio
import platform
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Any
from loguru import logger
import traceback

# PDF转换错误
class WordToPdfError(RuntimeError):
    pass


# PDF转换结果
@dataclass(frozen=True)
class WordToPdfResult:
    pdf_path: str # PDF文件路径
    backend: str # 转换所使用的后端

# PDF转换器
class WordToPdfConverter:
    def __init__(
        self,
        word_path: str, # Word文件路径
        *,
        output_pdf_path: Optional[str] = None, # 输出PDF文件路径
        prefer_backend: str = "auto", # 优先使用的后端
        soffice_path: Optional[str] = None, # LibreOffice可执行文件路径
        timeout_seconds: int = 300, # 转换超时时间（秒）
    ) -> None:
        self.word_path = str(word_path)
        self.output_pdf_path = str(output_pdf_path) if output_pdf_path else None
        self.prefer_backend = prefer_backend
        self.soffice_path = soffice_path
        self.timeout_seconds = int(timeout_seconds)

    # 主转换方法
    async def convert(self) -> WordToPdfResult:
        word = Path(self.word_path)
        # 检查Word文件是否存在且是文件
        if not word.exists() or not word.is_file():
            raise WordToPdfError(f"Word file not found: {self.word_path}")
        # 检查Word文件是否为.doc或.docx
        suffix = word.suffix.lower()
        if suffix not in {".doc", ".docx"}:
            raise WordToPdfError(f"Unsupported file type: {suffix}")
        
        out_pdf = (
            Path(self.output_pdf_path)
            if self.output_pdf_path
            else word.with_suffix(".pdf")
        )
        out_pdf.parent.mkdir(parents=True, exist_ok=True)

        backend = self._select_backend()
        if backend == "office_com":
            await self._convert_via_office_com(word, out_pdf)
        elif backend == "libreoffice":
            await self._convert_via_libreoffice(word, out_pdf)
        else:
            raise WordToPdfError(f"Unknown backend selected: {backend}")

        if not out_pdf.exists() or out_pdf.stat().st_size == 0:
            raise WordToPdfError("Conversion finished but output PDF is missing/empty")

        return WordToPdfResult(pdf_path=str(out_pdf), backend=backend) # 转换结果

    # 选择转换后端,自动模式下优先选择Office COM（仅Windows），然后是LibreOffice
    def _select_backend(self) -> str:
        prefer = (self.prefer_backend or "auto").lower()
        if prefer not in {"auto", "office_com", "libreoffice"}:
            raise WordToPdfError(
                "prefer_backend must be one of: auto, office_com, libreoffice"
            )

        if prefer != "auto":
            if prefer == "office_com" and not self._is_windows():
                raise WordToPdfError("office_com backend requires Windows")
            return prefer

        # 首先尝试Office COM（如果在Windows上且可用）
        if self._is_windows() and self._can_import_win32com():
            return "office_com"

        # 如果Office COM不可用，尝试LibreOffice
        if self._find_soffice() is not None:
            return "libreoffice"

        # 如果两个后端都不可用，在Windows上仍然尝试Office COM但提供更好的错误信息
        if self._is_windows():
            # 即使检测不到COM组件，也返回office_com让后续代码尝试，这样可以提供更具体的错误信息
            if not self._can_import_win32com():
                logger.warning("pywin32可能未正确安装，但仍尝试使用Office COM")
                return "office_com"
            else:
                raise WordToPdfError(
                    "No available backend. Install pywin32 + Microsoft Word, "
                    "or install LibreOffice and ensure soffice is in PATH."
                )

        raise WordToPdfError(
            "No available backend. Install LibreOffice and ensure soffice is in PATH."
        )

    @staticmethod
    def _is_windows() -> bool:
        return platform.system().lower() == "windows"

    @staticmethod
    def _can_import_win32com() -> bool:
        try:
            __import__("win32com.client")
            return True
        except Exception:
            return False

    def _find_soffice(self) -> Optional[str]:
        if self.soffice_path:
            p = Path(self.soffice_path)
            return str(p) if p.exists() else None

        which = shutil.which("soffice") or shutil.which("soffice.exe")
        return which

    async def _convert_via_libreoffice(self, word: Path, out_pdf: Path) -> None:
        soffice = self._find_soffice()
        if not soffice:
            raise WordToPdfError(
                "LibreOffice backend selected but soffice was not found"
            )

        with tempfile.TemporaryDirectory(prefix="word2pdf_") as tmpdir:
            tmpdir_p = Path(tmpdir)

            cmd = [
                soffice,
                "--headless",
                "--nologo",
                "--nolockcheck",
                "--nodefault",
                "--norestore",
                "--invisible",
                "--convert-to",
                "pdf",
                "--outdir",
                str(tmpdir_p),
                str(word),
            ]

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=self.timeout_seconds
                )
            except asyncio.TimeoutError as e:
                proc.kill()
                raise WordToPdfError(
                    f"LibreOffice conversion timed out after {self.timeout_seconds}s"
                ) from e

            if proc.returncode != 0:
                raise WordToPdfError(
                    "LibreOffice conversion failed. "
                    f"stdout={stdout.decode(errors='ignore')}; "
                    f"stderr={stderr.decode(errors='ignore')}"
                )

            produced = tmpdir_p / f"{word.stem}.pdf"
            if not produced.exists():
                candidates = list(tmpdir_p.glob("*.pdf"))
                if len(candidates) == 1:
                    produced = candidates[0]
                else:
                    raise WordToPdfError(
                        "LibreOffice reported success but produced PDF was not found"
                    )

            if out_pdf.exists():
                out_pdf.unlink()
            shutil.move(str(produced), str(out_pdf))

    async def _convert_via_office_com(self, word: Path, out_pdf: Path) -> None:
        if not self._is_windows():
            raise WordToPdfError("Office COM conversion requires Windows")
        if not self._can_import_win32com():
            raise WordToPdfError("pywin32 (win32com) is required for Office COM backend")

        # 重试机制 - 最多重试3次
        max_retries = 3
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                logger.info(f"开始Word转PDF，尝试 #{attempt + 1}: {word.name}")
                # Word COM automation is blocking and must run in a worker thread.
                await asyncio.wait_for(
                    asyncio.to_thread(self._office_com_export_pdf_sync, word, out_pdf),
                    timeout=self.timeout_seconds,
                )
                logger.info(f"Word转PDF成功，完成于尝试 #{attempt + 1}: {word.name}")
                return  # 成功则退出循环
            except Exception as e:
                last_exception = e
                logger.warning(f"Word转PDF尝试 #{attempt + 1} 失败: {str(e)}")
                if attempt < max_retries - 1:  # 不是最后一次尝试
                    logger.info(f"准备进行下一次尝试，等待片刻...")
                    await asyncio.sleep(1)  # 等待一秒再重试
                
        # 所有重试都失败了，抛出最后一次的异常
        raise WordToPdfError(f"Word转PDF经过{max_retries}次尝试后仍失败: {last_exception}")

    @staticmethod
    def _office_com_export_pdf_sync(word: Path, out_pdf: Path) -> None:
        import pythoncom
        import win32com.client
        import time

        # 初始化COM库
        try:
            pythoncom.CoInitialize()
        except Exception as e:
            logger.warning(f"COM初始化失败: {e}，可能已初始化")
        
        word_app = None
        doc = None
        try:
            # 启动Word应用程序
            word_app = win32com.client.DispatchEx("Word.Application")
            word_app.Visible = False
            word_app.DisplayAlerts = 0
            
            # 等待Word完全加载
            time.sleep(0.5)

            # 打开文档前验证文件存在
            if not word.exists():
                raise WordToPdfError(f"Word文件不存在: {str(word)}")
            
            # 以只读模式打开文档
            doc = word_app.Documents.Open(
                str(word), 
                ReadOnly=True,
                AddToRecentFiles=False,
                Visible=False
            )
            
            # 确保文档已完全加载
            word_app.ScreenUpdating = False
            
            # 尝试多种导出选项以提高兼容性
            try:
                doc.ExportAsFixedFormat(
                    OutputFileName=str(out_pdf),
                    ExportFormat=17,  # wdExportFormatPDF
                    OpenAfterExport=False,
                    OptimizeFor=0,    # wdOptimizeForPrint
                    CreateBookmarks=1, # wdExportCreateHeadingBookmarks
                    DocStructureTags=True,
                    BitmapMissingFonts=True,
                    UseDocumentPrintSettings=True,
                )
                logger.info(f"Word转PDF成功: {str(word)} -> {str(out_pdf)}")
            except Exception as export_error:
                # 如果默认导出失败，尝试使用更简单的选项
                logger.warning(f"Word PDF导出第一次尝试失败: {export_error}")
                try:
                    doc.ExportAsFixedFormat(
                        OutputFileName=str(out_pdf),
                        ExportFormat=17,
                        OpenAfterExport=False,
                    )
                    logger.info(f"Word转PDF成功（简化选项）: {str(word)} -> {str(out_pdf)}")
                except Exception as simple_export_error:
                    # 如果简单导出也失败，尝试关闭文档再重新打开
                    logger.warning(f"Word PDF导出第二次尝试失败: {simple_export_error}")
                    try:
                        if doc is not None:
                            doc.Close(False)
                            doc = None
                    except Exception as close_error:
                        logger.warning(f"关闭文档时发生错误: {close_error}")
                        doc = None
                    
                    # 重新打开文档
                    doc = word_app.Documents.Open(
                        str(word), 
                        ReadOnly=True,
                        AddToRecentFiles=False,
                        Visible=False
                    )
                    
                    # 再次尝试导出
                    doc.ExportAsFixedFormat(
                        OutputFileName=str(out_pdf),
                        ExportFormat=17,
                        OpenAfterExport=False,
                    )
                    logger.info(f"Word转PDF成功（重试）: {str(word)} -> {str(out_pdf)}")
                    
        except WordToPdfError:
            # 重新抛出我们的自定义异常
            raise
        except Exception as e:
            logger.error(f"Office COM转换失败详细信息: {str(e)}")
            logger.error(f"Word文件路径: {str(word)}")
            logger.error(f"输出PDF路径: {str(out_pdf)}")
            logger.error(f"错误类型: {type(e).__name__}")
            raise WordToPdfError(f"Office COM conversion failed: {e}")
        finally:
            # 清理资源
            try:
                # 安全地关闭文档
                if doc is not None:
                    try:
                        doc.Close(False)
                        logger.debug("文档已关闭")
                    except Exception as close_error:
                        logger.warning(f"关闭文档时发生错误: {close_error}")
                    finally:
                        doc = None
            except Exception as e:
                logger.warning(f"处理文档关闭时出错: {e}")
            
            try:
                # 安全地退出Word应用程序
                if word_app is not None:
                    try:
                        word_app.Quit()
                        logger.debug("Word应用程序已退出")
                    except Exception as quit_error:
                        logger.warning(f"退出Word应用程序时发生错误: {quit_error}")
                    finally:
                        word_app = None
            except Exception as e:
                logger.warning(f"处理Word应用程序退出时出错: {e}")
            
            try:
                pythoncom.CoUninitialize()
                logger.debug("COM库已卸载")
            except Exception:
                # CoUninitialize可能会在某些情况下失败，这通常不是严重问题
                pass
