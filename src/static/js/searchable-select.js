document.addEventListener("DOMContentLoaded", function () {
    initSimpleSearchableSelects();
    initEnhancedSearchableSelects();
});

function initSimpleSearchableSelects() {
    const searchInputs = document.querySelectorAll(".select-search-input[data-select-target]");

    searchInputs.forEach(function (searchInput) {
        const select = document.getElementById(searchInput.dataset.selectTarget);

        if (!select) {
            return;
        }

        const options = Array.from(select.options);
        const emptyOption = options.find(function (option) {
            return !option.value;
        }) || null;

        const syncOptions = function () {
            const query = searchInput.value.trim().toLowerCase();

            options.forEach(function (option) {
                if (!option.value) {
                    option.hidden = false;
                    return;
                }

                const isVisible = !query || option.text.toLowerCase().includes(query);
                option.hidden = !isVisible;

                if (!isVisible && option.selected && emptyOption) {
                    emptyOption.selected = true;
                }
            });
        };

        searchInput.addEventListener("input", syncOptions);

        if (searchInput.form && searchInput.form === select.form) {
            searchInput.form.addEventListener("reset", function () {
                window.setTimeout(function () {
                    searchInput.value = "";
                    options.forEach(function (option) {
                        option.hidden = false;
                    });
                }, 0);
            });
        }

        syncOptions();
    });
}

function initEnhancedSearchableSelects() {
    const roots = Array.from(document.querySelectorAll("[data-enhanced-select]"));

    roots.forEach(function (root) {
        const select = root.querySelector("select");
        const input = root.querySelector("[data-role='input']");
        const dropdown = root.querySelector("[data-role='dropdown']");
        const list = root.querySelector("[data-role='list']");
        const empty = root.querySelector("[data-role='empty']");
        const filterButton = root.querySelector("[data-role='filter-button']");
        const filters = root.querySelector("[data-role='filters']");
        const chips = Array.from(root.querySelectorAll(".search-select-filter-chip[data-field]"));

        if (!select || !input || !dropdown || !list || !empty || !filterButton || !filters || !chips.length) {
            return;
        }

        const allOptions = Array.from(select.options).filter(function (option) {
            return option.value;
        });
        const placeholderOption = Array.from(select.options).find(function (option) {
            return !option.value;
        }) || null;

        const closeDropdown = function () {
            root.classList.remove("search-select-open");
            dropdown.hidden = true;
        };

        const openDropdown = function () {
            root.classList.add("search-select-open");
            dropdown.hidden = false;
        };

        const closeFilters = function () {
            filters.hidden = true;
            filterButton.classList.remove("is-active");
        };

        const toggleFilters = function () {
            const willOpen = filters.hidden;
            filters.hidden = !willOpen;
            filterButton.classList.toggle("is-active", willOpen);
            if (willOpen) {
                openDropdown();
            }
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

        const getSelectedOption = function () {
            return allOptions.find(function (option) {
                return option.value === select.value;
            }) || null;
        };

        const syncInputWithSelection = function () {
            const selectedOption = getSelectedOption();
            input.value = selectedOption ? selectedOption.text.trim() : "";
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
            });

            return button;
        };

        const renderOptions = function () {
            const query = input.value.trim().toLowerCase();
            const activeFields = getActiveFields();
            const selectedOption = getSelectedOption();
            const selectedText = selectedOption ? selectedOption.text.trim().toLowerCase() : "";
            const effectiveQuery = query && query !== selectedText ? query : "";

            list.innerHTML = "";

            const visibleOptions = allOptions.filter(function (option) {
                if (!effectiveQuery) {
                    return true;
                }

                return activeFields.some(function (field) {
                    const value = (option.dataset[field] || option.text || "").toLowerCase();
                    return value.includes(effectiveQuery);
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
            toggleFilters();
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
            if (!root.contains(event.target)) {
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
    });
}
