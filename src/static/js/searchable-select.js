document.addEventListener("DOMContentLoaded", function () {
    const selects = Array.from(document.querySelectorAll("select.select-input"));

    selects.forEach(function (select) {
        enhanceSelect(select);
    });
});

function enhanceSelect(select) {
    if (!select || select.dataset.searchEnhanced === "true") {
        return;
    }

    const options = Array.from(select.options);
    const valueOptions = options.filter(function (option) {
        return option.value;
    });

    if (!valueOptions.length) {
        return;
    }

    const wrapper = document.createElement("div");
    wrapper.className = "search-select";
    wrapper.dataset.enhancedSelect = "true";

    select.dataset.searchEnhanced = "true";
    select.classList.add("search-select-native");
    select.parentNode.insertBefore(wrapper, select);
    wrapper.appendChild(select);

    const control = document.createElement("div");
    control.className = "search-select-control";

    const input = document.createElement("input");
    input.type = "text";
    input.className = "search-select-input";
    input.dataset.role = "input";
    input.autocomplete = "off";
    input.placeholder = select.dataset.searchPlaceholder || getPlaceholder(select);

    const filterButton = document.createElement("button");
    filterButton.type = "button";
    filterButton.className = "search-select-filter-button";
    filterButton.dataset.role = "filter-button";
    filterButton.setAttribute("aria-label", "Открыть фильтр");
    filterButton.innerHTML = [
        '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">',
        '<path d="M4 6h16M7 12h10M10 18h4"></path>',
        "</svg>",
    ].join("");

    control.appendChild(input);
    control.appendChild(filterButton);
    wrapper.appendChild(control);

    const dropdown = document.createElement("div");
    dropdown.className = "search-select-dropdown";
    dropdown.dataset.role = "dropdown";
    dropdown.hidden = true;

    const list = document.createElement("div");
    list.className = "search-select-options";
    list.dataset.role = "list";

    const empty = document.createElement("div");
    empty.className = "search-select-empty";
    empty.dataset.role = "empty";
    empty.hidden = true;
    empty.textContent = "Ничего не найдено.";

    dropdown.appendChild(list);
    dropdown.appendChild(empty);
    wrapper.appendChild(dropdown);

    const filters = document.createElement("div");
    filters.className = "search-select-filters";
    filters.dataset.role = "filters";
    filters.hidden = true;

    const filtersTitle = document.createElement("span");
    filtersTitle.className = "search-select-filters-title";
    filtersTitle.textContent = "Искать по";

    const filtersList = document.createElement("div");
    filtersList.className = "search-select-filter-list";

    const searchFields = getSearchFields(select, valueOptions);
    const chips = searchFields.map(function (field) {
        const chip = document.createElement("button");
        chip.type = "button";
        chip.className = "search-select-filter-chip is-active";
        chip.dataset.field = field.key;
        chip.textContent = field.label;
        filtersList.appendChild(chip);
        return chip;
    });

    filters.appendChild(filtersTitle);
    filters.appendChild(filtersList);
    wrapper.appendChild(filters);

    const placeholderOption = options.find(function (option) {
        return !option.value;
    }) || null;

    const getSelectedOption = function () {
        return valueOptions.find(function (option) {
            return option.value === select.value;
        }) || null;
    };

    const syncInputWithSelection = function () {
        const selectedOption = getSelectedOption();
        input.value = selectedOption ? selectedOption.text.trim() : "";
    };

    const closeDropdown = function () {
        wrapper.classList.remove("search-select-open");
        dropdown.hidden = true;
    };

    const openDropdown = function () {
        wrapper.classList.add("search-select-open");
        dropdown.hidden = false;
    };

    const closeFilters = function () {
        filters.hidden = true;
        filterButton.classList.remove("is-active");
    };

    const getActiveFields = function () {
        return chips
            .filter(function (chip) {
                return chip.classList.contains("is-active");
            })
            .map(function (chip) {
                return chip.dataset.field;
            });
    };

    const createOptionButton = function (option) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "search-select-option";
        button.textContent = option.text.trim();

        if (option.value === select.value) {
            button.classList.add("is-selected");
        }

        button.addEventListener("click", function () {
            select.value = option.value;
            syncInputWithSelection();
            closeDropdown();
            closeFilters();
            select.dispatchEvent(new Event("change", { bubbles: true }));
        });

        return button;
    };

    const renderOptions = function () {
        const query = input.value.trim().toLowerCase();
        const selectedOption = getSelectedOption();
        const selectedText = selectedOption ? selectedOption.text.trim().toLowerCase() : "";
        const effectiveQuery = query && query !== selectedText ? query : "";
        const activeFields = getActiveFields();

        list.innerHTML = "";

        const visibleOptions = valueOptions.filter(function (option) {
            if (!effectiveQuery) {
                return true;
            }

            return activeFields.some(function (field) {
                const haystack = getOptionSearchValue(option, field).toLowerCase();
                return haystack.includes(effectiveQuery);
            });
        });

        if (selectedOption && effectiveQuery) {
            select.value = placeholderOption ? placeholderOption.value : "";
        }

        visibleOptions.forEach(function (option) {
            list.appendChild(createOptionButton(option));
        });

        empty.hidden = visibleOptions.length > 0;
    };

    input.addEventListener("focus", function () {
        openDropdown();
        renderOptions();
    });

    input.addEventListener("click", function () {
        openDropdown();
        renderOptions();
    });

    input.addEventListener("input", function () {
        openDropdown();
        renderOptions();
    });

    input.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
            closeDropdown();
            closeFilters();
            syncInputWithSelection();
        }
    });

    filterButton.addEventListener("click", function (event) {
        event.preventDefault();
        event.stopPropagation();
        const shouldOpen = filters.hidden;
        filters.hidden = !shouldOpen;
        filterButton.classList.toggle("is-active", shouldOpen);
        if (shouldOpen) {
            openDropdown();
        }
        renderOptions();
    });

    chips.forEach(function (chip) {
        chip.addEventListener("click", function () {
            const activeChips = chips.filter(function (item) {
                return item.classList.contains("is-active");
            });

            if (chip.classList.contains("is-active") && activeChips.length === 1) {
                return;
            }

            chip.classList.toggle("is-active");
            renderOptions();
        });
    });

    document.addEventListener("click", function (event) {
        if (!wrapper.contains(event.target)) {
            closeDropdown();
            closeFilters();
            syncInputWithSelection();
        }
    });

    if (select.form) {
        select.form.addEventListener("reset", function () {
            window.setTimeout(function () {
                chips.forEach(function (chip) {
                    chip.classList.add("is-active");
                });
                syncInputWithSelection();
                renderOptions();
                closeDropdown();
                closeFilters();
            }, 0);
        });
    }

    syncInputWithSelection();
    renderOptions();
}

function getPlaceholder(select) {
    const selectedOption = select.options[select.selectedIndex];
    if (selectedOption && selectedOption.value) {
        return selectedOption.text.trim();
    }

    const placeholderOption = Array.from(select.options).find(function (option) {
        return !option.value;
    });

    const placeholderText = placeholderOption ? placeholderOption.text.trim() : "";
    if (!placeholderText || placeholderText === "---------") {
        return "Нажмите, чтобы выбрать";
    }

    return placeholderText;
}

function getSearchFields(select, options) {
    if (select.dataset.searchFields) {
        return select.dataset.searchFields.split(",").map(function (entry) {
            const parts = entry.split(":");
            const key = (parts[0] || "text").trim();
            const label = (parts[1] || getDefaultFieldLabel(key)).trim();
            return { key: key, label: label };
        });
    }

    const optionWithDataset = options.find(function (option) {
        return Object.keys(option.dataset).length > 0;
    });

    if (optionWithDataset) {
        return Object.keys(optionWithDataset.dataset).map(function (key) {
            return { key: key, label: getDefaultFieldLabel(key) };
        });
    }

    return [{ key: "text", label: "Тексту" }];
}

function getDefaultFieldLabel(key) {
    const labels = {
        text: "Тексту",
        title: "Названию",
        inventory: "Номеру",
        name: "ФИО",
        email: "Email",
        department: "Отделу",
        location: "Локации",
        category: "Категории",
        status: "Статусу",
    };

    return labels[key] || key;
}

function getOptionSearchValue(option, field) {
    if (field === "text") {
        return option.text || "";
    }

    return option.dataset[field] || option.text || "";
}
