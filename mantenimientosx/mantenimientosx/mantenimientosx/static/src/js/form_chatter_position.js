/** @odoo-module **/

import { FormRenderer } from "@web/views/form/form_renderer"
import { patch } from "@web/core/utils/patch"

// Parche para el FormRenderer para mover el chatter a la derecha
patch(FormRenderer.prototype, {
  setup() {
    super.setup()
    this.state = {
      ...this.state,
      chatterPosition: "right",
    }
  },
})
