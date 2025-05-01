function create_custom_dropdowns() {
    $('select').each(function (i, select) {
        if (!$(this).next().hasClass('dropdown-select')) {
            $(this).after('<div class="dropdown-select wide ' + ($(this).attr('class') || '') + '" tabindex="0"><span class="current"></span><div class="list"><ul></ul></div></div>');
            var dropdown = $(this).next();
            var options = $(select).find('option');
            var selected = $(this).find('option:selected');
            dropdown.find('.current').html(selected.data('display-text') || selected.text());
            options.each(function (j, o) {
                var display = $(o).data('display-text') || '';
                dropdown.find('ul').append('<li class="option ' + ($(o).is(':selected') ? 'selected' : '') + '" data-value="' + $(o).val() + '" data-display-text="' + display + '">' + $(o).text() + '</li>');
            });
        }
    });

    // Attach search box to each dropdown individually
    $('.dropdown-select .list ul').each(function (i) {
        if ($(this).prev('.dd-search').length === 0) {
            $(this).before('<div class="dd-search"><input autocomplete="off" onkeyup="filter(this)" class="dd-searchbox" type="text" placeholder="Search..."></div>');
        }
    });
}

// Update filter function to work per dropdown
function filter(input) {
    var valThis = $(input).val();
    var list = $(input).closest('.dropdown-select').find('ul > li');
    list.each(function () {
        var text = $(this).text();
        (text.toLowerCase().indexOf(valThis.toLowerCase()) > -1) ? $(this).show() : $(this).hide();
    });
}

// Event listeners

// Open/close dropdown
$(document).on('click', '.dropdown-select', function (event) {
    if ($(event.target).hasClass('dd-searchbox')) {
        return;
    }
    $('.dropdown-select').not(this).removeClass('open');  // Only close others
    $(this).toggleClass('open');
    if ($(this).hasClass('open')) {
        $(this).find('.option').attr('tabindex', 0);
        $(this).find('.selected').focus();
    } else {
        $(this).find('.option').removeAttr('tabindex');
        $(this).focus();
    }
});

// Close when clicking outside
$(document).on('click', function (event) {
    if ($(event.target).closest('.dropdown-select').length === 0) {
        $('.dropdown-select').removeClass('open');
        $('.dropdown-select .option').removeAttr('tabindex');
    }
});

// Option click - Fix here
$(document).on('click', '.dropdown-select .option', function (event) {
    var $dropdown = $(this).closest('.dropdown-select');  // Only this dropdown
    $dropdown.find('.selected').removeClass('selected');
    $(this).addClass('selected');
    var text = $(this).data('display-text') || $(this).text();
    $dropdown.find('.current').text(text);
    $dropdown.prev('select').val($(this).data('value')).trigger('change');
});

// Keyboard events
$(document).on('keydown', '.dropdown-select', function (event) {
    var focused_option = $($(this).find('.list .option:focus')[0] || $(this).find('.list .option.selected')[0]);
    if (event.keyCode == 13) { // Enter
        if ($(this).hasClass('open')) {
            focused_option.trigger('click');
        } else {
            $(this).trigger('click');
        }
        return false;
    } else if (event.keyCode == 40) { // Down arrow
        if (!$(this).hasClass('open')) {
            $(this).trigger('click');
        } else {
            focused_option.nextAll(':visible').first().focus();
        }
        return false;
    } else if (event.keyCode == 38) { // Up arrow
        if (!$(this).hasClass('open')) {
            $(this).trigger('click');
        } else {
            focused_option.prevAll(':visible').first().focus();
        }
        return false;
    } else if (event.keyCode == 27) { // Escape
        if ($(this).hasClass('open')) {
            $(this).trigger('click');
        }
        return false;
    }
});

$(document).ready(function () {
    create_custom_dropdowns();
});

$(document).ready(function () {
    function updateDropdown(url, requestType, selectedValue, targetDropdownIds) {
        $.ajax({
            type: 'POST',
            url: url,
            contentType: 'application/json',
            data: JSON.stringify({
                drop_down_data_request_type: requestType,
                current_dropdown_selection: selectedValue
            }),
            success: function (data) {
                targetDropdownIds.forEach(function (dropdownId) {
                    const selectEl = $('#' + dropdownId);
                    const previousValue = selectEl.val();  // store current selection
                    const newOptions = data.dropdown_data;
            
                    // Clear and repopulate
                    selectEl.empty().append('<option value="">Select</option>');
                    newOptions.forEach(function (val) {
                        selectEl.append(`<option value="${val}">${val}</option>`);
                    });
            
                    // Restore previous value if it's still valid
                    if (previousValue && newOptions.includes(previousValue)) {
                        selectEl.val(previousValue);
                    }
            
                    // Refresh custom dropdown (if any)
                    selectEl.next('.dropdown-select').remove();
                    create_custom_dropdowns();
                });
            },
            error: function (xhr, status, error) {
                console.error("Dropdown update error:", error);
            }
        });
    }
    
    // Train → Boarding & Deboarding
    $('#train').on('change', function () {
        const selectedTrain = $(this).val();
        if (selectedTrain) {
            updateDropdown('/get_dropdown_data', 'station', selectedTrain, ['boarding', 'deboarding']);
        }
    });
    
    // Boarding or Deboarding → Train
    $('#boarding, #deboarding').on('change', function () {
        const selectedStation = $(this).val();
        if (selectedStation) {
            updateDropdown('/get_dropdown_data', 'train', selectedStation, ['train']);
        }
    });
});