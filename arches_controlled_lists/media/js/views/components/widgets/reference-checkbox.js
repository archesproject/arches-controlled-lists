import ko from "knockout";
import ReferenceCheckboxViewModel from "viewmodels/reference-checkbox";
import referenceCheckboxTemplate from "templates/views/components/widgets/reference-checkbox.htm";

export default ko.components.register("reference-checkbox-widget", {
    viewModel: ReferenceCheckboxViewModel,
    template: referenceCheckboxTemplate,
});
