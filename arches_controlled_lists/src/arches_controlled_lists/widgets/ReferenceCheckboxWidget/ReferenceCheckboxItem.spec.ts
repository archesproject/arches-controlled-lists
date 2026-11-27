import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import PrimeVue from "primevue/config";

import ReferenceCheckboxItem from "@/arches_controlled_lists/widgets/ReferenceCheckboxWidget/components/ReferenceCheckboxItem.vue";

import type { ReferenceSelectTreeNode } from "@/arches_controlled_lists/datatypes/reference-select/types.ts";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeItem(overrides: {
    key?: string;
    label?: string;
    guide?: boolean;
    children?: ReferenceSelectTreeNode[];
}): ReferenceSelectTreeNode {
    return {
        key: overrides.key ?? "item-1",
        label: overrides.label ?? "Option A",
        children: overrides.children ?? [],
        data: {
            guide: overrides.guide ?? false,
            list_item_id: overrides.key ?? "item-1",
            display_value: overrides.label ?? "Option A",
            uri: "http://example.com/item-1",
            sortorder: 0,
            list_item_values: [
                {
                    id: "val-1",
                    language_id: "en",
                    list_item_id: overrides.key ?? "item-1",
                    value: overrides.label ?? "Option A",
                    valuetype_id: "prefLabel",
                },
            ],
            children: [],
        },
    };
}

const BASE_PROPS = {
    multiple: true,
    selectedIds: new Set<string>(),
    radioGroupName: "test-radio-group",
};

function mountItem(props: object) {
    return mount(ReferenceCheckboxItem, {
        props: props as InstanceType<typeof ReferenceCheckboxItem>["$props"],
        global: { plugins: [PrimeVue] },
    });
}

// ---------------------------------------------------------------------------
// Guide item rendering
// ---------------------------------------------------------------------------

describe("guide item", () => {
    it("renders a section label, not a checkbox or radio", () => {
        const wrapper = mountItem({
            ...BASE_PROPS,
            item: makeItem({ guide: true }),
        });

        expect(wrapper.find(".reference-checkbox-section").exists()).toBe(true);
        expect(wrapper.find(".reference-checkbox-section-label").text()).toBe(
            "Option A",
        );
        expect(wrapper.find("input[type=checkbox]").exists()).toBe(false);
        expect(wrapper.find("input[type=radio]").exists()).toBe(false);
    });

    it("renders children of a guide item", () => {
        const child = makeItem({ key: "child-1", label: "Child A" });
        const wrapper = mountItem({
            ...BASE_PROPS,
            item: makeItem({ guide: true, children: [child] }),
        });

        const childLabels = wrapper.findAll("label");
        expect(childLabels.some((l) => l.text() === "Child A")).toBe(true);
    });

    it("renders no children container when guide item has no children", () => {
        const wrapper = mountItem({
            ...BASE_PROPS,
            item: makeItem({ guide: true }),
        });

        expect(wrapper.find(".reference-checkbox-children").exists()).toBe(
            false,
        );
    });
});

// ---------------------------------------------------------------------------
// Selectable item — checkbox mode (multiple=true)
// ---------------------------------------------------------------------------

describe("selectable item, checkbox mode", () => {
    it("renders a checkbox", () => {
        const wrapper = mountItem({
            ...BASE_PROPS,
            multiple: true,
            item: makeItem({}),
        });

        expect(wrapper.find(".reference-checkbox-item").exists()).toBe(true);
        expect(wrapper.find("input[type=checkbox]").exists()).toBe(true);
        expect(wrapper.find("input[type=radio]").exists()).toBe(false);
    });

    it("emits update:selectedIds adding the item key on check", async () => {
        const wrapper = mountItem({
            ...BASE_PROPS,
            multiple: true,
            selectedIds: new Set<string>(),
            item: makeItem({ key: "item-1" }),
        });

        // PrimeVue Checkbox emits update:modelValue with the new boolean.
        await wrapper
            .findComponent({ name: "Checkbox" })
            .vm.$emit("update:modelValue", true);

        const emitted = wrapper.emitted("update:selectedIds") as [
            Set<string>,
        ][];
        expect(emitted).toHaveLength(1);
        expect(emitted[0][0]).toEqual(new Set(["item-1"]));
    });

    it("emits update:selectedIds removing the item key on uncheck", async () => {
        const wrapper = mountItem({
            ...BASE_PROPS,
            multiple: true,
            selectedIds: new Set(["item-1"]),
            item: makeItem({ key: "item-1" }),
        });

        await wrapper
            .findComponent({ name: "Checkbox" })
            .vm.$emit("update:modelValue", false);

        const emitted = wrapper.emitted("update:selectedIds") as [
            Set<string>,
        ][];
        expect(emitted[0][0].has("item-1")).toBe(false);
    });

    it("does not remove other selected items when unchecking one", async () => {
        const wrapper = mountItem({
            ...BASE_PROPS,
            multiple: true,
            selectedIds: new Set(["item-1", "item-2"]),
            item: makeItem({ key: "item-1" }),
        });

        await wrapper
            .findComponent({ name: "Checkbox" })
            .vm.$emit("update:modelValue", false);

        const emitted = wrapper.emitted("update:selectedIds") as [
            Set<string>,
        ][];
        const result = emitted[0][0];
        expect(result.has("item-1")).toBe(false);
        expect(result.has("item-2")).toBe(true);
    });
});

// ---------------------------------------------------------------------------
// Selectable item — radio mode (multiple=false)
// ---------------------------------------------------------------------------

describe("selectable item, radio mode", () => {
    it("renders a radio button, not a checkbox", () => {
        const wrapper = mountItem({
            ...BASE_PROPS,
            multiple: false,
            item: makeItem({}),
        });

        expect(wrapper.find("input[type=radio]").exists()).toBe(true);
        expect(wrapper.find("input[type=checkbox]").exists()).toBe(false);
    });

    it("emits a Set with only this item's key when selected", async () => {
        const wrapper = mountItem({
            ...BASE_PROPS,
            multiple: false,
            selectedIds: new Set(["other-item"]),
            item: makeItem({ key: "item-1" }),
        });

        await wrapper
            .findComponent({ name: "RadioButton" })
            .vm.$emit("update:modelValue", "item-1");

        const emitted = wrapper.emitted("update:selectedIds") as [
            Set<string>,
        ][];
        expect(emitted[0][0]).toEqual(new Set(["item-1"]));
    });
});

// ---------------------------------------------------------------------------
// Children propagation
// ---------------------------------------------------------------------------

describe("children propagation", () => {
    it("renders an indented children container for a selectable item with children", () => {
        const child = makeItem({ key: "child-1", label: "Child A" });
        const wrapper = mountItem({
            ...BASE_PROPS,
            item: makeItem({ children: [child] }),
        });

        expect(wrapper.find(".reference-checkbox-indented").exists()).toBe(
            true,
        );
    });

    it("bubbles child update:selectedIds to parent", async () => {
        const child = makeItem({ key: "child-1", label: "Child A" });
        const wrapper = mountItem({
            ...BASE_PROPS,
            multiple: true,
            item: makeItem({ children: [child] }),
        });

        // Trigger the child's checkbox (inside the indented container) directly.
        const childCheckbox = wrapper
            .find(".reference-checkbox-indented")
            .findComponent({ name: "Checkbox" });
        await childCheckbox.vm.$emit("update:modelValue", true);

        const emitted = wrapper.emitted("update:selectedIds") as [
            Set<string>,
        ][];
        expect(emitted[0][0]).toEqual(new Set(["child-1"]));
    });

    it("renders no indented container when selectable item has no children", () => {
        const wrapper = mountItem({
            ...BASE_PROPS,
            item: makeItem({}),
        });

        expect(wrapper.find(".reference-checkbox-indented").exists()).toBe(
            false,
        );
    });
});
