import type { InjectionKey, Ref } from "vue";
import type { Language } from "@/arches_vue_utils/types";
import type {
    ControlledList,
    ControlledListItem,
} from "@/arches_references/types";

// Injection keys
type DisplayedRowRef = Ref<ControlledList | ControlledListItem | null>;
export const displayedRowKey = Symbol() as InjectionKey<DisplayedRowRef>;
type ItemRef = Ref<ControlledListItem>;
export const itemKey = Symbol() as InjectionKey<ItemRef>;
type LanguageRef = Ref<Language>;
export const selectedLanguageKey = Symbol() as InjectionKey<LanguageRef>;
export const systemLanguageKey = Symbol() as InjectionKey<Language>;

// Constants
export const NOTE = "note";
export const URI = "URI";
export const CONTRAST = "contrast";
export const ERROR = "error";
export const DANGER = "danger";
export const PRIMARY = "primary";
export const SECONDARY = "secondary";
export const SUCCESS = "success";
export const DEFAULT_ERROR_TOAST_LIFE = 8000;

// Django model choices
export const METADATA_CHOICES = {
    title: "title",
    alternativeText: "alt",
    description: "desc",
    attribution: "attr",
};

export const NOTE_CHOICES = {
    scope: "scopeNote",
    definition: "definition",
    example: "example",
    history: "historyNote",
    editorial: "editorialNote",
    change: "changeNote",
    note: "note",
    description: "description",
};

// Temporary workaround until received from backend
export const ENGLISH = {
    code: "en",
    default_direction: "ltr" as const,
    id: 1,
    isdefault: true,
    name: "English",
    scope: "system",
};
