"""Bilingual error envelope and shared exception hierarchy.

Mirrors the standard error format from the master spec:
    { error: { code, message_fr, message_ar, detail, ... } }
"""

from fastapi import Request
from fastapi.responses import JSONResponse


class UcarError(Exception):
    """Base for all domain errors. Subclasses set http_status, code, message_fr."""

    http_status: int = 500
    code: str = "INTERNAL_ERROR"
    message_fr: str = "Une erreur interne est survenue."
    message_ar: str = "حدث خطأ داخلي."

    def __init__(self, detail: str = "", **extra):
        super().__init__(detail)
        self.detail = detail
        self.extra = extra


class ValidationFailed(UcarError):
    http_status = 422
    code = "VALIDATION_FAILED"
    message_fr = "Les données fournies sont invalides."
    message_ar = "البيانات المقدمة غير صالحة."


class PermissionDenied(UcarError):
    http_status = 403
    code = "PERMISSION_DENIED"
    message_fr = "Vous n'avez pas les droits nécessaires pour cette action."
    message_ar = "ليس لديك الصلاحيات اللازمة لهذا الإجراء."


class NotFound(UcarError):
    http_status = 404
    code = "NOT_FOUND"
    message_fr = "La ressource demandée est introuvable."
    message_ar = "المورد المطلوب غير موجود."


class TenantScopeViolation(UcarError):
    http_status = 403
    code = "TENANT_SCOPE_VIOLATION"
    message_fr = "Accès refusé : vous ne pouvez pas accéder aux données d'un autre établissement."
    message_ar = "تم رفض الوصول: لا يمكنك الوصول إلى بيانات مؤسسة أخرى."


class IntegrationFailed(UcarError):
    http_status = 502
    code = "INTEGRATION_FAILED"
    message_fr = "Erreur de communication avec un service externe."
    message_ar = "خطأ في التواصل مع خدمة خارجية."


class FileTooLarge(UcarError):
    http_status = 413
    code = "FILE_TOO_LARGE"
    message_fr = "Ce fichier dépasse la taille maximale autorisée de 50 Mo."
    message_ar = "يتجاوز هذا الملف الحجم الأقصى المسموح به وهو 50 ميغابايت."


class UnsupportedFormat(UcarError):
    http_status = 415
    code = "UNSUPPORTED_FORMAT"
    message_fr = "Ce format de fichier n'est pas accepté. Utilisez Excel, PDF, CSV ou une image."
    message_ar = "صيغة الملف هذه غير مقبولة. استخدم Excel أو PDF أو CSV أو صورة."


class ImageResolutionTooLow(UcarError):
    http_status = 422
    code = "IMAGE_RESOLUTION_TOO_LOW"
    message_fr = "La qualité de l'image est insuffisante. Numérisez à 300 DPI minimum ou photographiez sous meilleure lumière."
    message_ar = "جودة الصورة غير كافية. يرجى المسح الضوئي بدقة 300 DPI على الأقل."


class PeriodLocked(UcarError):
    http_status = 409
    code = "PERIOD_LOCKED"
    message_fr = "Cette période a été verrouillée. Contactez l'administration centrale de l'UCAR."
    message_ar = "تم قفل هذه الفترة. يرجى التواصل مع الإدارة المركزية للجامعة."


class CommitConflict(UcarError):
    http_status = 409
    code = "COMMIT_CONFLICT"
    message_fr = "Des données existent déjà pour cet établissement et cette période. Choisissez : remplacer, fusionner ou annuler."
    message_ar = "توجد بيانات بالفعل لهذه المؤسسة وهذه الفترة. اختر: استبدال أو دمج أو إلغاء."


class SessionExpired(UcarError):
    http_status = 401
    code = "SESSION_EXPIRED"
    message_fr = "Votre session a expiré. Vos données ont été sauvegardées automatiquement."
    message_ar = "انتهت صلاحية جلستك. تم حفظ بياناتك تلقائياً."


class PdfTooManyPages(UcarError):
    http_status = 422
    code = "PDF_TOO_MANY_PAGES"
    message_fr = "Ce PDF dépasse 30 pages. Veuillez le découper en plusieurs fichiers avant de le soumettre."
    message_ar = "يتجاوز هذا الملف 30 صفحة. يرجى تقسيمه إلى ملفات أصغر قبل الإرسال."


async def ucar_error_handler(request: Request, exc: UcarError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.http_status,
        content={
            "error": {
                "code": exc.code,
                "message_fr": exc.message_fr,
                "message_ar": exc.message_ar,
                "detail": exc.detail,
                **exc.extra,
            }
        },
    )
