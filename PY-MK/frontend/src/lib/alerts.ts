import Swal, { type SweetAlertOptions } from "sweetalert2";

/*
 * Avisos y confirmaciones de toda la aplicacion.
 *
 * - Confirmar, eliminar, aprobar y los errores son DIALOGOS: piden una decision o
 *   avisan de algo que no se puede ignorar. SweetAlert2 da el foco atrapado, Escape
 *   y la vuelta del foco al boton que lo abrio.
 * - Exito, informacion y advertencia son TOASTS: no bloquean, se cierran solos y el
 *   lector de pantalla los anuncia (role=status).
 *
 * Los iconos son SVG propios (trazos de lucide) en lugar de las animaciones de
 * SweetAlert2, que se dibujaban rotas con el tema (un check que parecia una X).
 * La API publica no cambia: las llamadas existentes siguen funcionando.
 */

type Tono = "info" | "success" | "warning" | "danger";

const TRAZOS: Record<Tono, string> = {
  info: '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
  success: '<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
  warning:
    '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
  danger:
    '<path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><path d="M10 11v6"/><path d="M14 11v6"/>',
};

const ERROR_TRAZO = '<circle cx="12" cy="12" r="10"/><path d="m15 9-6 6"/><path d="m9 9 6 6"/>';

function icono(tono: Tono, trazo = TRAZOS[tono]): string {
  return `<span class="ns-dialog-icon ns-tone-${tono}"><svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${trazo}</svg></span>`;
}

const animacionPropia: Pick<SweetAlertOptions, "showClass" | "hideClass"> = {
  showClass: { popup: "ns-dialog-in", backdrop: "ns-backdrop-in" },
  hideClass: { popup: "ns-dialog-out", backdrop: "ns-backdrop-out" },
};

type DialogBase = Pick<SweetAlertOptions, "showClass" | "hideClass" | "buttonsStyling" | "focusCancel" | "customClass">;

function dialogo(tono: Tono, confirmVariant: string): DialogBase {
  return {
    ...animacionPropia,
    buttonsStyling: false,
    focusCancel: tono === "danger",
    customClass: {
      popup: `ns-dialog ns-tone-${tono}`,
      icon: "ns-dialog-icon-slot",
      title: "ns-dialog-title",
      htmlContainer: "ns-dialog-text",
      actions: "ns-dialog-actions",
      confirmButton: `button ${confirmVariant}`,
      cancelButton: "button button-ghost",
      input: "ns-dialog-input",
      validationMessage: "ns-dialog-validation",
    },
  };
}

const toast = Swal.mixin({
  toast: true,
  position: "top-end",
  showConfirmButton: false,
  showCloseButton: true,
  closeButtonAriaLabel: "Cerrar aviso",
  timerProgressBar: false,
  ...animacionPropia,
  didOpen: (el) => {
    el.setAttribute("role", "status");
    el.setAttribute("aria-live", "polite");
    el.addEventListener("mouseenter", Swal.stopTimer);
    el.addEventListener("mouseleave", Swal.resumeTimer);
  },
});

function avisar(tono: Tono, title: string, text: string | undefined, timer: number) {
  return toast.fire({
    title,
    text,
    timer,
    iconHtml: icono(tono),
    customClass: {
      popup: `ns-toast ns-tone-${tono}`,
      icon: "ns-toast-icon-slot",
      title: "ns-toast-title",
      htmlContainer: "ns-toast-text",
      closeButton: "ns-toast-close",
    },
  });
}

function escapar(texto: string): string {
  return texto.replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`);
}

type ConfirmOptions = {
  title?: string;
  text?: string;
  confirmText?: string;
  cancelText?: string;
};

// ── Confirmación genérica ──────────────────────────────────────────────
export async function confirmAction({
  title = "Confirmar acción",
  text = "Esta acción no se puede deshacer.",
  confirmText = "Confirmar",
  cancelText = "Cancelar",
}: ConfirmOptions) {
  const result = await Swal.fire({
    ...dialogo("warning", "button-primary"),
    iconHtml: icono("warning"),
    title,
    text,
    showCancelButton: true,
    confirmButtonText: confirmText,
    cancelButtonText: cancelText,
    reverseButtons: true,
  });
  return result.isConfirmed;
}

// ── Confirmación de ELIMINAR ──────────────────────────────────────────
export async function confirmDelete({
  title = "¿Eliminar este registro?",
  text = "Se eliminará de forma permanente. No se puede deshacer.",
  confirmText = "Eliminar",
  cancelText = "Cancelar",
}: ConfirmOptions = {}) {
  const result = await Swal.fire({
    ...dialogo("danger", "button-danger"),
    iconHtml: icono("danger"),
    title,
    text,
    showCancelButton: true,
    confirmButtonText: confirmText,
    cancelButtonText: cancelText,
    reverseButtons: true,
  });
  return result.isConfirmed;
}

// ── Confirmación ESTRICTA — hay que escribir un valor para habilitarla ─
export async function confirmDeleteStrict({
  title,
  text,
  expected,
  inputLabel = "Escribe el valor para confirmar:",
  confirmText = "Eliminar definitivamente",
  cancelText = "Cancelar",
}: {
  title: string;
  text: string;
  expected: string;
  inputLabel?: string;
  confirmText?: string;
  cancelText?: string;
}) {
  const result = await Swal.fire({
    ...dialogo("danger", "button-danger"),
    iconHtml: icono("danger"),
    title,
    html: `<p>${escapar(text)}</p><p class="ns-dialog-hint">${escapar(inputLabel)} <strong>${escapar(expected)}</strong></p>`,
    input: "text",
    inputAttributes: { autocapitalize: "off", autocorrect: "off", "aria-label": inputLabel },
    showCancelButton: true,
    confirmButtonText: confirmText,
    cancelButtonText: cancelText,
    reverseButtons: true,
    preConfirm: (value) => {
      if (value !== expected) {
        Swal.showValidationMessage("El valor escrito no coincide.");
        return false;
      }
      return true;
    },
  });
  return result.isConfirmed;
}

// ── Confirmación de APROBAR ───────────────────────────────────────────
export async function confirmApprove({
  title = "¿Aprobar este elemento?",
  text = "Una vez aprobado, el cambio será visible de inmediato.",
  confirmText = "Aprobar",
  cancelText = "Cancelar",
}: ConfirmOptions = {}) {
  const result = await Swal.fire({
    ...dialogo("success", "button-success"),
    iconHtml: icono("success"),
    title,
    text,
    showCancelButton: true,
    confirmButtonText: confirmText,
    cancelButtonText: cancelText,
    reverseButtons: true,
  });
  return result.isConfirmed;
}

// ── Avisos ────────────────────────────────────────────────────────────
export function notifySuccess(title: string, text?: string) {
  return avisar("success", title, text, 3000);
}

/** Un error pide que la persona lo lea: es un dialogo, no un toast. */
export function notifyError(title: string, text?: string) {
  return Swal.fire({
    ...dialogo("danger", "button-primary"),
    iconHtml: icono("danger", ERROR_TRAZO),
    title,
    text,
    confirmButtonText: "Entendido",
  });
}

export function notifyWarning(title: string, text?: string) {
  return avisar("warning", title, text, 4500);
}

export function notifyInfo(title: string, text?: string) {
  return avisar("info", title, text, 3000);
}
