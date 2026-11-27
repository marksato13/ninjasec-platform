import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

type EmptyStateProps = {
  icon: LucideIcon;
  title: string;
  /** Una linea: que falta y que pasa cuando exista. */
  description?: string;
  /** Acción principal (normalmente el mismo boton de crear de la cabecera). */
  action?: { label: string; onClick: () => void };
  /** Contenido extra bajo la acción (p. ej. un enlace secundario). */
  children?: ReactNode;
};

/**
 * Estado vacío de una lista: dice que no hay nada todavía y ofrece el siguiente paso.
 * Usa el mismo borde discontinuo que `.empty-state` para no introducir otro lenguaje.
 */
export function EmptyState({ icon: Icon, title, description, action, children }: EmptyStateProps) {
  return (
    <div className="empty-state empty-state--rich" role="status">
      <span className="empty-state__icon" aria-hidden="true">
        <Icon size={20} strokeWidth={1.75} />
      </span>
      <p className="empty-state__title">{title}</p>
      {description ? <p className="empty-state__text">{description}</p> : null}
      {action ? (
        <button className="button button-primary button-sm" type="button" onClick={action.onClick}>
          {action.label}
        </button>
      ) : null}
      {children}
    </div>
  );
}
