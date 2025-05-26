odoo.define("mantenimientosx.gantt", (require) => {
  var core = require("web.core")
  var _t = core._t
  var $ = require("jquery")
 

  // Inicialización cuando el documento está listo
  $(document).ready(() => {
    console.log("Inicializando script de Gantt")

    // Inicializar tooltips de Bootstrap
    $('[data-toggle="tooltip"]').tooltip()

    // Inicializar datepickers para las fechas
    if ($.fn.datepicker) {
      $(".datepicker").datepicker({
        dateFormat: "dd/mm/yy",
        dayNames: ["Domingo", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"],
        dayNamesMin: ["Do", "Lu", "Ma", "Mi", "Ju", "Vi", "Sa"],
        monthNames: [
          "Enero",
          "Febrero",
          "Marzo",
          "Abril",
          "Mayo",
          "Junio",
          "Julio",
          "Agosto",
          "Septiembre",
          "Octubre",
          "Noviembre",
          "Diciembre",
        ],
        monthNamesShort: ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"],
        firstDay: 1,
        changeMonth: true,
        changeYear: true,
        yearRange: "c-10:c+10",
        showButtonPanel: true,
        currentText: "Hoy",
        closeText: "Cerrar",
      })
    }

    // Actualizar el enlace de exportación cuando cambian las fechas, aqui puede ocurrir un salto. 
    $("#fecha_inicio, #fecha_fin").on("change", () => {
      var fechaInicio = $("#fecha_inicio").val() || ""
      var fechaFin = $("#fecha_fin").val() || ""

      var url =
        "/mantenimientosx/excel_export?fecha_inicio=" +
        encodeURIComponent(fechaInicio) +
        "&fecha_fin=" +
        encodeURIComponent(fechaFin) +
        "&t=" +
        new Date().getTime() // Añadir timestamp para evitar caché

      $("#link-export-excel").attr("href", url)
    })

    // Actualizar también el enlace directo cuando cambian las fechas
    /*$("#fecha_inicio, #fecha_fin").on("change", () => {
      var fechaInicio = $("#fecha_inicio").val() || ""
      var fechaFin = $("#fecha_fin").val() || ""

      var url =
        "/mantenimientosx/excel_export?fecha_inicio=" +
        encodeURIComponent(fechaInicio) +
        "&fecha_fin=" +
        encodeURIComponent(fechaFin)

      $("#link-export-excel").attr("href", url)
    })*/

    // Función de búsqueda mejorada con animación
    function buscarEnTabla() {
      var texto = $("#gantt-search").val().toLowerCase()
      console.log("Buscando: " + texto)

      // Mostrar indicador de búsqueda
      $(".search-icon").removeClass("fa-search").addClass("fa-spinner fa-spin")

      setTimeout(() => {
        if (texto.length === 0) {
          // Mostrar todas las filas si no hay texto de búsqueda
          $(".gantt-table tbody tr").show()

          // Restaurar icono de búsqueda
          $(".search-icon").removeClass("fa-spinner fa-spin").addClass("fa-search")
          return
        }

        // Ocultar todas las filas primero
        $(".gantt-table tbody tr").hide()

        // Buscar en filas de máquinas
        $(".gantt-table tbody tr.maquina-row").each(function () {
          var maquina = $(this).find(".maquina-cell").text().toLowerCase()

          if (maquina.indexOf(texto) !== -1) {
            // Mostrar la fila de la máquina y todas sus actividades
            $(this).show()

            // Encontrar y mostrar todas las filas de actividad que siguen hasta la próxima máquina
            var $nextRows = $(this).nextUntil(".maquina-row")
            $nextRows.show()
          }
        })

        // Buscar en filas de actividades
        $(".gantt-table tbody tr.actividad-row").each(function () {
          var actividad = $(this).find(".actividad-cell").text().toLowerCase()

          if (actividad.indexOf(texto) !== -1) {
            // Mostrar la fila de actividad
            $(this).show()

            // Mostrar la fila de la máquina correspondiente (anterior)
            var $prevMaquina = $(this).prevAll(".maquina-row").first()
            $prevMaquina.show()
          }
        })

        // Restaurar icono de búsqueda
        $(".search-icon").removeClass("fa-spinner fa-spin").addClass("fa-search")

        // Mostrar mensaje si no hay resultados
        if ($(".gantt-table tbody tr:visible").length === 0) {
          // Crear una fila para el mensaje de no resultados
          var colCount = $(".gantt-table thead th").length
          var noResultsRow =
            '<tr class="no-results"><td colspan="' +
            colCount +
            '" class="text-center py-3">No se encontraron resultados para "<strong>' +
            texto +
            '</strong>"</td></tr>'

          // Eliminar mensaje anterior si existe
          $(".gantt-table tbody tr.no-results").remove()

          // Añadir mensaje
          $(".gantt-table tbody").append(noResultsRow)
        }
      }, 300) 
    }

    // Asignar eventos de búsqueda
    $("#btn-search").on("click", () => {
      buscarEnTabla()
    })

    $("#gantt-search").on("keyup", function (e) {
      if (e.key === "Enter") {
        buscarEnTabla()
      }

      // Búsqueda en tiempo real después de 500ms de inactividad
      clearTimeout($(this).data("timeout"))
      if ($(this).val().length >= 3 || $(this).val().length === 0) {
        $(this).data(
          "timeout",
          setTimeout(() => {
            buscarEnTabla()
          }, 500),
        )
      }
    })

    // Limpiar búsqueda cuando se hace clic en el icono
    $(".search-icon").on("click", () => {
      if ($("#gantt-search").val().length > 0) {
        $("#gantt-search").val("")
        buscarEnTabla()
      }
    })

    // Manejar el envío del formulario de filtro con validación
    $("#gantt-filter-form").on("submit", function (e) {
      e.preventDefault()

      var fechaInicio = $("#fecha_inicio").val()
      var fechaFin = $("#fecha_fin").val()

      // Validar fechas
      if (!fechaInicio || !fechaFin) {
        // Mostrar alerta de error
        var alertHtmlDate =
          '<div class="alert alert-danger alert-dismissible fade show mt-3" role="alert">' +
          '<i class="fas fa-exclamation-triangle mr-2"></i> Por favor, ingrese ambas fechas' +
          '<button type="button" class="close" data-dismiss="alert" aria-label="Close">' +
          '<span aria-hidden="true">&times;</span></button></div>'

        // Eliminar alertas anteriores
        $(".date-filter .alert").remove()

        // Insertar alerta después del formulario
        $(this).after(alertHtmlDate)
        return
      }

      // Validar que fecha fin sea mayor o igual a fecha inicio
      try {
        var inicio = $.datepicker.parseDate("dd/mm/yy", fechaInicio)
        var fin = $.datepicker.parseDate("dd/mm/yy", fechaFin)

        if (fin < inicio) {
          // Mostrar alerta de error
          var alertHtmlDateRange =
            '<div class="alert alert-danger alert-dismissible fade show mt-3" role="alert">' +
            '<i class="fas fa-exclamation-triangle mr-2"></i> La fecha fin debe ser mayor o igual a la fecha inicio' +
            '<button type="button" class="close" data-dismiss="alert" aria-label="Close">' +
            '<span aria-hidden="true">&times;</span></button></div>'

          // Eliminar alertas anteriores
          $(".date-filter .alert").remove()

          // Insertar alerta después del formulario
          $(this).after(alertHtmlDateRange)
          return
        }
      } catch (e) {
        console.error("Error al parsear fechas:", e)
      }

      // Mostrar indicador de carga en el botón
      var $btn = $(this).find("button[type='submit']")
      var originalHtml = $btn.html()
      $btn.html('<i class="fas fa-spinner fa-spin"></i> Cargando...')
      $btn.prop("disabled", true)

      // Redirigir con los parámetros de fecha
      window.location.href =
        "/mantenimientosx/gantt?fecha_inicio=" +
        encodeURIComponent(fechaInicio) +
        "&fecha_fin=" +
        encodeURIComponent(fechaFin)
    })

    // Hacer que la tabla sea más interactiva
    $(".gantt-table .maquina-row").on("click", function () {
      // Toggle para mostrar/ocultar actividades de esta máquina
      var $nextRows = $(this).nextUntil(".maquina-row")
      $nextRows.toggle()

      // Cambiar icono o estilo para indicar expansión/colapso
      $(this).toggleClass("expanded")
    })

    // Añadir tooltips a las celdas con datos
    $(".gantt-table td[class*='estado-']").each(function () {
      var estado = ""
      if ($(this).hasClass("estado-normal")) estado = "Normal"
      else if ($(this).hasClass("estado-proximo")) estado = "Próximo"
      else if ($(this).hasClass("estado-atrasado")) estado = "Atrasado"
      else if ($(this).hasClass("estado-pendiente")) estado = "Orden Pendiente"

      var docId = $(this).text().trim()
      if (docId) {
        $(this).attr("title", estado + ": " + docId)
        $(this).attr("data-toggle", "tooltip")
        $(this).css("cursor", "pointer")
      }
    })

    // Inicializar tooltips
    $('[data-toggle="tooltip"]').tooltip()

    // Añadir efecto hover a las filas
    $(".gantt-table tr").hover(
      function () {
        $(this).addClass("table-hover")
      },
      function () {
        $(this).removeClass("table-hover")
      },
    )

    // Añadir efecto de resaltado a las celdas al hacer hover
    $(".gantt-table td[class*='estado-']").hover(
      function () {
        $(this).css("opacity", "0.8")
      },
      function () {
        $(this).css("opacity", "1")
      },
    )

    // Detectar si estamos en un dispositivo móvil
    var isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent)
    if (isMobile) {
      // Ajustes específicos para móviles
      $(".gantt-table").addClass("table-sm")
      $(".control-panel").addClass("p-2")
    }

    console.log("Script de Gantt inicializado correctamente")
  })
})
