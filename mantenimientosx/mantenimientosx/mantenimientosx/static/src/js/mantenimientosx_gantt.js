odoo.define("mantenimientosx.gantt", (require) => {
    var core = require("web.core");
    var _t = core._t;
    var $ = require("jquery");

    // Inicialización cuando el documento está listo
    $(document).ready(() => {
        console.log("Inicializando script de Gantt");

        // Inicializar tooltips de Bootstrap
        $('[data-toggle="tooltip"]').tooltip();

        // Inicializar datepickers para las fechas
        if ($.fn.datepicker) {
            $(".datepicker").datepicker({
                dateFormat: "dd/mm/yy",
                dayNames: ["Domingo", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"],
                dayNamesMin: ["Do", "Lu", "Ma", "Mi", "Ju", "Vi", "Sa"],
                monthNames: [
                    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
                ],
                monthNamesShort: ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"],
                firstDay: 1,
                changeMonth: true,
                changeYear: true,
                yearRange: "c-10:c+10",
                showButtonPanel: true,
                currentText: "Hoy",
                closeText: "Cerrar",
            });
        }

        // Actualizar el enlace de exportación cuando cambian las fechas
        $("#fecha_inicio, #fecha_fin").on("change", () => {
            var fechaInicio = $("#fecha_inicio").val() || "";
            var fechaFin = $("#fecha_fin").val() || "";
            var url =
                "/mantenimientosx/excel_export?fecha_inicio=" +
                encodeURIComponent(fechaInicio) +
                "&fecha_fin=" +
                encodeURIComponent(fechaFin) +
                "&t=" +
                new Date().getTime(); // Añadir timestamp para evitar caché
            $("#link-export-excel").attr("href", url);
        });

        // -------- Buscador tipo Ctrl+F --------
        let lastResults = [];
        let lastActiveIdx = -1;

        function limpiarBuscador() {
            $(".gantt-table td, .gantt-table th, .gantt-table .maquina-cell, .gantt-table .actividad-cell").removeClass("highlight-search highlight-active-search");
            $(".gantt-table tr").removeClass("found-row");
            lastResults = [];
            lastActiveIdx = -1;
        }

        function buscarEnTabla() {
            limpiarBuscador();
            var texto = $("#gantt-search").val().toLowerCase().trim();
            if (!texto) return;

            // Resalta coincidencias en todas las celdas relevantes
            $(".gantt-table td, .gantt-table th, .gantt-table .maquina-cell, .gantt-table .actividad-cell").each(function(){
                var $el = $(this);
                var val = $el.text().toLowerCase();
                if (val.includes(texto)) {
                    $el.addClass("highlight-search");
                    $el.closest("tr").addClass("found-row").show(); // mostrar la fila
                    // Guardar referencia para saltar con enter
                    lastResults.push($el);
                }
            });
            // También muestra la fila de máquina para cada actividad encontrada
            $(".gantt-table tr.found-row").each(function(){
                if ($(this).hasClass("actividad-row")) {
                    $(this).prevAll(".maquina-row").first().show();
                }
            });

            // Si hay resultados, poner el primero como activo
            if (lastResults.length > 0) {
                lastActiveIdx = 0;
                lastResults[0].addClass("highlight-active-search");
                // Scroll a la coincidencia
                $('html, body').animate({
                    scrollTop: lastResults[0].offset().top - 150
                }, 300);
            } else {
                // Si no hay resultados, mostrar todas las filas
                $(".gantt-table tbody tr").show();
            }
        }

        function nextResultado() {
            if (!lastResults.length) return;
            lastResults[lastActiveIdx].removeClass("highlight-active-search");
            lastActiveIdx = (lastActiveIdx + 1) % lastResults.length;
            lastResults[lastActiveIdx].addClass("highlight-active-search");
            $('html, body').animate({
                scrollTop: lastResults[lastActiveIdx].offset().top - 150
            }, 300);
        }

        // Buscar con Enter y saltar coincidencias con Enter repetido
        $("#gantt-search").on("keydown", function(e){
            if (e.key === "Enter") {
                if (lastResults.length === 0) {
                    buscarEnTabla();
                } else {
                    nextResultado();
                }
                e.preventDefault();
            }
        });

        // Buscar con la lupa
        $("#btn-search").on("click", function(){
            buscarEnTabla();
            $("#gantt-search").focus();
        });

        // Limpiar resaltados si cambias el texto
        $("#gantt-search").on("input", function(){
            limpiarBuscador();
        });

        // CSS para el resaltado
        const style = document.createElement('style');
        style.innerHTML = `
            .highlight-search {
                background: #ffe3f2 !important;
                color: #ad2274 !important;
                font-weight: 700;
            }
            .highlight-active-search {
                background: #ffbde0 !important;
                color: #bb164e !important;
                font-weight: 900;
                border: 2px solid #ff83be !important;
            }
        `;
        document.head.appendChild(style);

        // ---------------- Fin Buscador tipo Ctrl+F ----------------

        // Limpiar búsqueda cuando se hace clic en el icono (esto borra el texto y limpia resaltado)
        $(".search-icon").on("click", () => {
            if ($("#gantt-search").val().length > 0) {
                $("#gantt-search").val("");
                limpiarBuscador();
            }
        });

        // Manejar el envío del formulario de filtro con validación
        $("#gantt-filter-form").on("submit", function (e) {
            e.preventDefault();

            var fechaInicio = $("#fecha_inicio").val();
            var fechaFin = $("#fecha_fin").val();

            // Validar fechas
            if (!fechaInicio || !fechaFin) {
                // Mostrar alerta de error
                var alertHtmlDate =
                    '<div class="alert alert-danger alert-dismissible fade show mt-3" role="alert">' +
                    '<i class="fas fa-exclamation-triangle mr-2"></i> Por favor, ingrese ambas fechas' +
                    '<button type="button" class="close" data-dismiss="alert" aria-label="Close">' +
                    '<span aria-hidden="true">&times;</span></button></div>';

                // Eliminar alertas anteriores
                $(".date-filter .alert").remove();

                // Insertar alerta después del formulario
                $(this).after(alertHtmlDate);
                return;
            }

            // Validar que fecha fin sea mayor o igual a fecha inicio
            try {
                var inicio = $.datepicker.parseDate("dd/mm/yy", fechaInicio);
                var fin = $.datepicker.parseDate("dd/mm/yy", fechaFin);

                if (fin < inicio) {
                    // Mostrar alerta de error
                    var alertHtmlDateRange =
                        '<div class="alert alert-danger alert-dismissible fade show mt-3" role="alert">' +
                        '<i class="fas fa-exclamation-triangle mr-2"></i> La fecha fin debe ser mayor o igual a la fecha inicio' +
                        '<button type="button" class="close" data-dismiss="alert" aria-label="Close">' +
                        '<span aria-hidden="true">&times;</span></button></div>';

                    // Eliminar alertas anteriores
                    $(".date-filter .alert").remove();

                    // Insertar alerta después del formulario
                    $(this).after(alertHtmlDateRange);
                    return;
                }
            } catch (e) {
                console.error("Error al parsear fechas:", e);
            }

            // Mostrar indicador de carga en el botón
            var $btn = $(this).find("button[type='submit']");
            var originalHtml = $btn.html();
            $btn.html('<i class="fas fa-spinner fa-spin"></i> Cargando...');
            $btn.prop("disabled", true);

            // Redirigir con los parámetros de fecha
            window.location.href =
                "/mantenimientosx/gantt?fecha_inicio=" +
                encodeURIComponent(fechaInicio) +
                "&fecha_fin=" +
                encodeURIComponent(fechaFin);
        });

        // Hacer que la tabla sea más interactiva
        $(".gantt-table .maquina-row").on("click", function () {
            // Toggle para mostrar/ocultar actividades de esta máquina
            var $nextRows = $(this).nextUntil(".maquina-row");
            $nextRows.toggle();

            // Cambiar icono o estilo para indicar expansión/colapso
            $(this).toggleClass("expanded");
        });

        // Añadir tooltips a las celdas con datos
        $(".gantt-table td[class*='estado-']").each(function () {
            var estado = "";
            if ($(this).hasClass("estado-normal")) estado = "Normal";
            else if ($(this).hasClass("estado-proximo")) estado = "Próximo";
            else if ($(this).hasClass("estado-atrasado")) estado = "Atrasado";
            else if ($(this).hasClass("estado-pendiente")) estado = "Orden Pendiente";

            var docId = $(this).text().trim();
            if (docId) {
                $(this).attr("title", estado + ": " + docId);
                $(this).attr("data-toggle", "tooltip");
                $(this).css("cursor", "pointer");
            }
        });

        // Inicializar tooltips
        $('[data-toggle="tooltip"]').tooltip();

        // Añadir efecto hover a las filas
        $(".gantt-table tr").hover(
            function () {
                $(this).addClass("table-hover");
            },
            function () {
                $(this).removeClass("table-hover");
            }
        );

        // Añadir efecto de resaltado a las celdas al hacer hover
        $(".gantt-table td[class*='estado-']").hover(
            function () {
                $(this).css("opacity", "0.8");
            },
            function () {
                $(this).css("opacity", "1");
            }
        );

        // Detectar si estamos en un dispositivo móvil
        var isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
        if (isMobile) {
            // Ajustes específicos para móviles
            $(".gantt-table").addClass("table-sm");
            $(".control-panel").addClass("p-2");
        }

        console.log("Script de Gantt inicializado correctamente");
    });
});
