<script setup lang="ts">
import { ref } from "vue";
import { useGettext } from "vue3-gettext";

import { Form, FormField } from "@primevue/forms";
import { useToast } from "primevue/usetoast";
import Button from "primevue/button";
import InputFile from "primevue/fileupload";
import Message from "primevue/message";
import RadioButton from "primevue/radiobutton";

import type { FormFieldResolverOptions } from "@primevue/forms";

import { importList } from "@/arches_controlled_lists/api.ts";
import {
    DEFAULT_ERROR_TOAST_LIFE,
    ERROR,
} from "@/arches_controlled_lists/constants.ts";

const { $gettext } = useGettext();
const toast = useToast();

const emit = defineEmits<{
    (e: "imported"): void;
    (e: "cancel"): void;
}>();

const formRef = ref();
const file = ref<File | null>(null);
const overwriteOption = ref();

const overwriteOptions = ref([
    {
        label: $gettext("Ignore"),
        value: "ignore",
        tooltip: $gettext("Do nothing if the list or list item already exist"),
    },
    {
        label: $gettext("Duplicate"),
        value: "duplicate",
        tooltip: $gettext(
            "Create a new list or list item if it already exists",
        ),
    },
    {
        label: $gettext("Overwrite"),
        value: "overwrite",
        tooltip: $gettext(
            "If a list already exists, replace it with the new one",
        ),
    },
]);

function updateFileValue(event: { files: File[] }) {
    if (event.files && event.files.length > 0) {
        file.value = event.files[0];
    } else {
        file.value = null;
    }
}

async function submit() {
    const isValid = await formRef.value?.validate();
    if (!isValid || !file.value) {
        return;
    }
    await importList(file.value, overwriteOption.value)
        .then(() => {
            emit("imported");
        })
        .catch((error: Error) => {
            toast.add({
                severity: ERROR,
                life: DEFAULT_ERROR_TOAST_LIFE,
                summary: $gettext("Unable to import SKOS file"),
                detail: error.message,
            });
        });
}

function fileResolver() {
    const errors = [];
    if (!file.value) {
        errors.push({ message: $gettext("Please select a file") });
    } else if (!file.value.name.toLowerCase().endsWith(".xml")) {
        errors.push({ message: $gettext("File must be an XML file") });
    }
    return { errors };
}

function overwriteResolver(formFieldVal: FormFieldResolverOptions) {
    const value = formFieldVal.value;
    const errors = [];
    if (!value) {
        errors.push({ message: $gettext("Please select an overwrite option") });
    }
    return { errors };
}
</script>

<template>
    <Form
        ref="formRef"
        class="form"
        @submit="submit"
    >
        <label for="fileUpload">SKOS File</label>
        <FormField
            v-slot="$field"
            name="fileUpload"
            :resolver="fileResolver"
            class="form-fields"
        >
            <InputFile
                v-model="file"
                accept=".xml"
                mode="basic"
                :auto="false"
                :choose-label="$gettext('Choose File')"
                :multiple="false"
                @select="updateFileValue"
            />
            <Message
                v-for="error in $field.errors"
                :key="error.message"
                severity="error"
                size="small"
            >
                {{ error.message }}
            </Message>
        </FormField>

        <label for="overwrite-options">Overwrite Options</label>
        <FormField
            v-slot="$field"
            name="overwrite-options"
            :resolver="overwriteResolver"
            class="form-fields"
        >
            <span
                v-for="option in overwriteOptions"
                :key="option.value"
                v-tooltip.bottom="{
                    value: option.tooltip,
                    showDelay: 1000,
                    hideDelay: 300,
                }"
                class="radio-button-and-label"
            >
                <RadioButton
                    v-model="overwriteOption"
                    :input-id="option.value"
                    :value="option.value"
                    :initial-value="option.value"
                    :aria-label="option.tooltip"
                />
                <label
                    :for="option.value"
                    class="radio-label"
                    >{{ option.label }}</label
                >
            </span>
            <Message
                v-for="error in $field.errors"
                :key="error.message"
                severity="error"
                size="small"
            >
                {{ error.message }}
            </Message>
        </FormField>
        <div class="p-dialog-footer">
            <Button
                label="Cancel"
                type="button"
                @click="$emit('cancel')"
            />
            <Button
                label="Upload File"
                type="submit"
            />
        </div>
    </Form>
</template>
<style scoped>
.form {
    margin-top: 1rem;
}
.p-dialog-footer {
    padding: 0;
    margin-top: 1rem;
}
.p-fileupload-basic {
    justify-content: flex-start;
}
.form-fields {
    padding-inline-start: 1rem;

    label {
        margin-bottom: 0;
    }
}
.radio-button-and-label {
    margin-right: 1.5rem;
    margin-bottom: 0.5rem;
}
.radio-label {
    margin-inline-start: 0.5rem;
}
</style>
