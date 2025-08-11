<script setup lang="ts">
import { ref } from "vue";
import { useGettext } from "vue3-gettext";

import { Form } from "@primevue/forms";

import Button from "primevue/button";
import InputFile from "primevue/fileupload";
import RadioButton from "primevue/radiobutton";

const { $gettext } = useGettext();

const formRef = ref();

const file = ref<File | null>(null);
const overwriteOption = ref("ignore");

const overwriteOptions = ref([
    { label: $gettext("Ignore"), value: "ignore" },
    { label: $gettext("Duplicate"), value: "duplicate" },
    { label: $gettext("Overwrite"), value: "overwrite" },
]);

function handleFileUpload(event: Event) {
    const target = event.target as HTMLInputElement;
    if (target.files && target.files.length > 0) {
        file.value = target.files[0];
    } else {
        file.value = null;
    }
}

function submit() {
    console.log("File:", file.value);
    console.log("Boolean:", overwriteOption.value);
}
</script>

<template>
    <Form
        ref="formRef"
        @submit="submit"
    >
        <label for="fileUpload">SKOS File</label>
        <FormField
            name="fileUpload"
            :resolver="resolver"
        >
            <InputFile
                v-model:file="file"
                accept=".xml"
                @change="handleFileUpload"
            />
        </FormField>

        <label for="overwrite-options">Overwrite Options</label>
        <FormField
            name="overwrite-options"
            :resolver="resolver"
        >
            <span v-for="option in overwriteOptions">
                <RadioButton
                    v-model="overwriteOption"
                    :input-id="option.value"
                    :value="option.value"
                />
                <label :for="option.value">{{ option.label }}</label>
            </span>
        </FormField>
        <Button
            label="Submit"
            type="submit"
        />
    </Form>
</template>
