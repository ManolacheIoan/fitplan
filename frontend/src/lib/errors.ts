import { ApiError } from "@/lib/api";

const MESSAGES: Record<string, string> = {
  invalid_credentials: "Email sau parolă incorectă.",
  email_taken: "Există deja un cont cu acest email.",
  too_many_attempts: "Prea multe încercări. Încearcă din nou peste câteva minute.",
  backend_unavailable: "Serverul nu răspunde. Încearcă din nou puțin mai târziu.",
  csrf_failed: "Sesiunea a expirat. Reîncarcă pagina.",
  not_authenticated: "Trebuie să te autentifici.",
  consent_required: "Este necesar consimțământul pentru a continua.",
  underage: "FitPlan este destinat exclusiv persoanelor de peste 18 ani.",
  age_out_of_range: "Verifică data nașterii.",
  sets_already_logged: "Ai deja serii înregistrate pentru acest exercițiu în antrenamentul de azi.",
  exercise_not_allowed: "Exercițiul ales nu poate înlocui acest exercițiu.",
  program_days_mismatch: "Programul ales nu este disponibil pentru acest număr de zile.",
  pregnancy_answer_required: "Te rugăm să răspunzi la toate întrebările.",
  weight_loss_blocked_bmi:
    "Pentru valorile introduse, obiectivul de slăbire nu este disponibil. Alege alt obiectiv și discută cu un medic sau un specialist acreditat.",
};

/** User-facing Romanian message for any thrown error. */
export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (typeof error.detail === "string" && MESSAGES[error.detail]) return MESSAGES[error.detail];
    if (error.status === 422) return "Unele câmpuri nu sunt valide. Verifică datele introduse.";
    if (error.status === 404) return "Nu am găsit ce căutai.";
  }
  return "A apărut o eroare. Încearcă din nou.";
}
