// document.addEventListener("DOMContentLoaded", function () {
//     /**
//      * HomePage - Help section
//      */
//     class Help {
//         constructor($el) {
//             this.$el = $el;
//             this.$buttonsContainer = $el.querySelector(".help--buttons");
//             this.$slidesContainers = $el.querySelectorAll(".help--slides");
//             this.currentSlide = this.$buttonsContainer.querySelector(".active").parentElement.dataset.id;
//             this.init();
//         }
//
//         init() {
//             this.events();
//         }
//
//         events() {
//             /**
//              * Slide buttons
//              */
//             this.$buttonsContainer.addEventListener("click", e => {
//                 if (e.target.classList.contains("btn")) {
//                     this.changeSlide(e);
//                 }
//             });
//
//             /**
//              * Pagination buttons
//              */
//             this.$el.addEventListener("click", e => {
//                 if (e.target.classList.contains("btn") && e.target.parentElement.parentElement.classList.contains("help--slides-pagination")) {
//                     this.changePage(e);
//                 }
//             });
//         }
//
//         changeSlide(e) {
//             e.preventDefault();
//             const $btn = e.target;
//
//             // Buttons Active class change
//             [...this.$buttonsContainer.children].forEach(btn => btn.firstElementChild.classList.remove("active"));
//             $btn.classList.add("active");
//
//             // Current slide
//             this.currentSlide = $btn.parentElement.dataset.id;
//
//             // Slides active class change
//             this.$slidesContainers.forEach(el => {
//                 el.classList.remove("active");
//
//                 if (el.dataset.id === this.currentSlide) {
//                     el.classList.add("active");
//                 }
//             });
//         }
//
//         /**
//          * TODO: callback to page change event
//          */
//         // changePage(e) {
//         //     e.preventDefault();
//         //     const page = e.target.dataset.page;
//         //
//         //     // Make an AJAX call to fetch the new content
//         //     fetch(`?page=${page}`)
//         //         .then(response => response.text())
//         //         .then(html => {
//         //             // Parse the HTML and update the content
//         //             const parser = new DOMParser();
//         //             const doc = parser.parseFromString(html, 'text/html');
//         //             const newContent = doc.querySelector('.help--slides.active .help--slides-items');
//         //             const newPagination = doc.querySelector('.help--slides-pagination');
//         //
//         //             // Replace old content with new content
//         //             const currentContainer = this.$el.querySelector('.help--slides.active .help--slides-items');
//         //             currentContainer.innerHTML = newContent.innerHTML;
//         //
//         //             // Replace old pagination with new pagination
//         //             const currentPagination = this.$el.querySelector('.help--slides-pagination');
//         //             currentPagination.innerHTML = newPagination.innerHTML;
//         //         })
//         //         .catch(error => console.error('Error loading new page:', error));
//         // }
//         changePage(e) {
//             e.preventDefault();
//             const $btn = e.target;
//             const page = $btn.dataset.page;
//             const listType = $btn.closest(".pagination").dataset.list;
//
//             fetch(`?page_${listType}=${page}`)
//                 .then(response => response.text())
//                 .then(html => {
//                     const parser = new DOMParser();
//                     const doc = parser.parseFromString(html, 'text/html');
//
//                     // Update the corresponding list
//                     const newContent = doc.querySelector(`.help--slides[data-id="${this.currentSlide}"] .help--slides-items`);
//                     const newPagination = doc.querySelector(`.pagination[data-list="${listType}"] .help--slides-pagination`);
//
//                     const currentContent = this.$el.querySelector(`.help--slides[data-id="${this.currentSlide}"] .help--slides-items`);
//                     const currentPagination = this.$el.querySelector(`.pagination[data-list="${listType}"] .help--slides-pagination`);
//
//                     currentContent.innerHTML = newContent.innerHTML;
//                     currentPagination.innerHTML = newPagination.innerHTML;
//
//                     // Reattach events after replacing content
//                     this.events();
//                 })
//                 .catch(error => console.error('Error loading new page:', error));
//         }
//     }
//
//     const helpSection = document.querySelector(".help");
//     if (helpSection !== null) {
//         new Help(helpSection);
//     }
//
//     /**
//      * Form Select
//      */
//     class FormSelect {
//         constructor($el) {
//             this.$el = $el;
//             this.options = [...$el.children];
//             this.init();
//         }
//
//         init() {
//             this.createElements();
//             this.addEvents();
//             this.$el.parentElement.removeChild(this.$el);
//         }
//
//         createElements() {
//             // Input for value
//             this.valueInput = document.createElement("input");
//             this.valueInput.type = "text";
//             this.valueInput.name = this.$el.name;
//
//             // Dropdown container
//             this.dropdown = document.createElement("div");
//             this.dropdown.classList.add("dropdown");
//
//             // List container
//             this.ul = document.createElement("ul");
//
//             // All list options
//             this.options.forEach((el, i) => {
//                 const li = document.createElement("li");
//                 li.dataset.value = el.value;
//                 li.innerText = el.innerText;
//
//                 if (i === 0) {
//                     // First clickable option
//                     this.current = document.createElement("div");
//                     this.current.innerText = el.innerText;
//                     this.dropdown.appendChild(this.current);
//                     this.valueInput.value = el.value;
//                     li.classList.add("selected");
//                 }
//
//                 this.ul.appendChild(li);
//             });
//
//             this.dropdown.appendChild(this.ul);
//             this.dropdown.appendChild(this.valueInput);
//             this.$el.parentElement.appendChild(this.dropdown);
//         }
//
//         addEvents() {
//             this.dropdown.addEventListener("click", e => {
//                 const target = e.target;
//                 this.dropdown.classList.toggle("selecting");
//
//                 // Save new value only when clicked on li
//                 if (target.tagName === "LI") {
//                     this.valueInput.value = target.dataset.value;
//                     this.current.innerText = target.innerText;
//                 }
//             });
//         }
//     }
//
//     document.querySelectorAll(".form-group--dropdown select").forEach(el => {
//         new FormSelect(el);
//     });
//
//     /**
//      * Hide elements when clicked on document
//      */
//     document.addEventListener("click", function (e) {
//         const target = e.target;
//         const tagName = target.tagName;
//
//         if (target.classList.contains("dropdown")) return false;
//
//         if (tagName === "LI" && target.parentElement.parentElement.classList.contains("dropdown")) {
//             return false;
//         }
//
//         if (tagName === "DIV" && target.parentElement.classList.contains("dropdown")) {
//             return false;
//         }
//
//         document.querySelectorAll(".form-group--dropdown .dropdown").forEach(el => {
//             el.classList.remove("selecting");
//         });
//     });
//
//     /**
//      * Switching between form steps
//      */
//     class FormSteps {
//         constructor(form) {
//             this.$form = form;
//             this.$next = form.querySelectorAll(".next-step");
//             this.$prev = form.querySelectorAll(".prev-step");
//             this.$step = form.querySelector(".form--steps-counter span");
//             this.currentStep = 1;
//
//             this.$stepInstructions = form.querySelectorAll(".form--steps-instructions p");
//             const $stepForms = form.querySelectorAll("form > div");
//             this.slides = [...this.$stepInstructions, ...$stepForms];
//
//             this.init();
//         }
//
//         /**
//          * Init all methods
//          */
//         init() {
//             this.events();
//             this.updateForm();
//         }
//
//         /**
//          * All events that are happening in form
//          */
//         events() {
//             // Next step
//             this.$next.forEach(btn => {
//                 btn.addEventListener("click", e => {
//                     e.preventDefault();
//                     this.currentStep++;
//                     this.updateForm();
//                 });
//             });
//
//             // Previous step
//             this.$prev.forEach(btn => {
//                 btn.addEventListener("click", e => {
//                     e.preventDefault();
//                     this.currentStep--;
//                     this.updateForm();
//                 });
//             });
//
//             // Form submit
//             this.$form.querySelector("form").addEventListener("submit", e => this.submit(e));
//         }
//
//         /**
//          * Update form front-end
//          * Show next or previous section etc.
//          */
//         updateForm() {
//             this.$step.innerText = this.currentStep;
//
//             // TODO: Validation
//
//             this.slides.forEach(slide => {
//                 slide.classList.remove("active");
//
//                 if (slide.dataset.step == this.currentStep) {
//                     slide.classList.add("active");
//                 }
//             });
//
//             this.$stepInstructions[0].parentElement.parentElement.hidden = this.currentStep >= 6;
//             this.$step.parentElement.hidden = this.currentStep >= 6;
//
//             // TODO: get data from inputs and show them in summary
//         }
//
//         /**
//          * Submit form
//          *
//          * TODO: validation, send data to server
//          */
//         submit(e) {
//             e.preventDefault();
//             this.currentStep++;
//             this.updateForm();
//         }
//     }
//
//     const form = document.querySelector(".form--steps");
//     if (form !== null) {
//         new FormSteps(form);
//     }
// });

document.addEventListener("DOMContentLoaded", function () {
    /**
     * HomePage - Help section
     */
    class Help {
        constructor($el) {
            this.$el = $el;
            this.$buttonsContainer = $el.querySelector(".help--buttons");
            this.$slidesContainers = $el.querySelectorAll(".help--slides");
            this.currentSlide = this.$buttonsContainer.querySelector(".active").parentElement.dataset.id;
            this.init();
        }

        init() {
            this.events();
        }

        events() {
            /**
             * Slide buttons
             */
            this.$buttonsContainer.addEventListener("click", e => {
                if (e.target.classList.contains("btn")) {
                    this.changeSlide(e);
                }
            });

            /**
             * Pagination buttons
             */
            this.$el.addEventListener("click", e => {
                if (e.target.classList.contains("btn") && e.target.parentElement.parentElement.classList.contains("help--slides-pagination")) {
                    this.changePage(e);
                }
            });
        }

        changeSlide(e) {
            e.preventDefault();
            const $btn = e.target;

            // Buttons Active class change
            [...this.$buttonsContainer.children].forEach(btn => btn.firstElementChild.classList.remove("active"));
            $btn.classList.add("active");

            // Current slide
            this.currentSlide = $btn.parentElement.dataset.id;

            // Slides active class change
            this.$slidesContainers.forEach(el => {
                el.classList.remove("active");

                if (el.dataset.id === this.currentSlide) {
                    el.classList.add("active");
                }
            });
        }

        changePage(e) {
            e.preventDefault();
            const $btn = e.target;
            const page = $btn.dataset.page;
            const listType = $btn.closest(".pagination").dataset.list;

            fetch(`?page_${listType}=${page}`)
                .then(response => response.text())
                .then(html => {
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, 'text/html');

                    // Update the corresponding list
                    const newContent = doc.querySelector(`.help--slides[data-id="${this.currentSlide}"] .help--slides-items`);
                    const newPagination = doc.querySelector(`.pagination[data-list="${listType}"] .help--slides-pagination`);

                    const currentContent = this.$el.querySelector(`.help--slides[data-id="${this.currentSlide}"] .help--slides-items`);
                    const currentPagination = this.$el.querySelector(`.pagination[data-list="${listType}"] .help--slides-pagination`);

                    currentContent.innerHTML = newContent.innerHTML;
                    currentPagination.innerHTML = newPagination.innerHTML;

                    // Reattach events after replacing content
                    this.events();
                })
                .catch(error => console.error('Error loading new page:', error));
        }
    }

    const helpSection = document.querySelector(".help");
    if (helpSection !== null) {
        new Help(helpSection);
    }

    /**
     * Form Select
     */
    class FormSelect {
        constructor($el) {
            this.$el = $el;
            this.options = [...$el.children];
            this.init();
        }

        init() {
            this.createElements();
            this.addEvents();
            this.$el.parentElement.removeChild(this.$el);
        }

        createElements() {
            // Input for value
            this.valueInput = document.createElement("input");
            this.valueInput.type = "text";
            this.valueInput.name = this.$el.name;

            // Dropdown container
            this.dropdown = document.createElement("div");
            this.dropdown.classList.add("dropdown");

            // List container
            this.ul = document.createElement("ul");

            // All list options
            this.options.forEach((el, i) => {
                const li = document.createElement("li");
                li.dataset.value = el.value;
                li.innerText = el.innerText;

                if (i === 0) {
                    // First clickable option
                    this.current = document.createElement("div");
                    this.current.innerText = el.innerText;
                    this.dropdown.appendChild(this.current);
                    this.valueInput.value = el.value;
                    li.classList.add("selected");
                }

                this.ul.appendChild(li);
            });

            this.dropdown.appendChild(this.ul);
            this.dropdown.appendChild(this.valueInput);
            this.$el.parentElement.appendChild(this.dropdown);
        }

        addEvents() {
            this.dropdown.addEventListener("click", e => {
                const target = e.target;
                this.dropdown.classList.toggle("selecting");

                // Save new value only when clicked on li
                if (target.tagName === "LI") {
                    this.valueInput.value = target.dataset.value;
                    this.current.innerText = target.innerText;
                }
            });
        }
    }

    document.querySelectorAll(".form-group--dropdown select").forEach(el => {
        new FormSelect(el);
    });

    /**
     * Hide elements when clicked on document
     */
    document.addEventListener("click", function (e) {
        const target = e.target;
        const tagName = target.tagName;

        if (target.classList.contains("dropdown")) return false;

        if (tagName === "LI" && target.parentElement.parentElement.classList.contains("dropdown")) {
            return false;
        }

        if (tagName === "DIV" && target.parentElement.classList.contains("dropdown")) {
            return false;
        }

        document.querySelectorAll(".form-group--dropdown .dropdown").forEach(el => {
            el.classList.remove("selecting");
        });
    });

    /**
     * Switching between form steps
     */
    class FormSteps {
        constructor(form) {
            this.$form = form;
            this.$next = form.querySelectorAll(".next-step");
            this.$prev = form.querySelectorAll(".prev-step");
            this.$step = form.querySelector(".form--steps-counter span");
            this.currentStep = 1;

            this.$stepInstructions = form.querySelectorAll(".form--steps-instructions p");
            const $stepForms = form.querySelectorAll("form > div");
            this.slides = [...this.$stepInstructions, ...$stepForms];

            // Initialize category data from Django template
            this.categories = Array.from(document.querySelectorAll('[name="categories"]:checked')).map(el => el.value);

            this.init();
        }

        init() {
            this.events();
            this.updateForm();
            this.populateSummary(); // Initialize summary on form load
        }

        events() {
            this.$next.forEach(btn => {
                btn.addEventListener("click", e => {
                    e.preventDefault();
                    this.currentStep++;
                    this.updateForm();
                });
            });

            this.$prev.forEach(btn => {
                btn.addEventListener("click", e => {
                    e.preventDefault();
                    this.currentStep--;
                    this.updateForm();
                });
            });

            // Handle category selection change
            document.querySelectorAll('[name="categories"]').forEach(el => {
                el.addEventListener("change", () => {
                    this.categories = Array.from(document.querySelectorAll('[name="categories"]:checked')).map(el => el.value);
                    this.filterOrganizations();
                    this.populateSummary(); // Update summary when categories change
                });
            });
        }

        updateForm() {
            this.$step.innerText = this.currentStep;

            // Show or hide form steps based on current step
            this.slides.forEach(slide => {
                slide.classList.remove("active");
                if (slide.dataset.step == this.currentStep) {
                    slide.classList.add("active");
                }
            });

            // Show or hide category-related organizations in step 3
            if (this.currentStep === 3) {
                this.filterOrganizations();
            }

            this.populateSummary(); // Update summary on form step change
        }

        filterOrganizations() {
            const organizations = document.querySelectorAll('[name="organization"]');

            organizations.forEach(org => {
                const orgCategories = JSON.parse(org.dataset.categories);

                if (this.categories.every(cat => orgCategories.includes(parseInt(cat)))) {
                    org.closest('.form-group--checkbox').style.display = 'block';
                } else {
                    org.closest('.form-group--checkbox').style.display = 'none';
                }
            });
        }

        // populateSummary() {
        //     // Collect form data and populate summary section
        //     const formData = {
        //         bags: document.querySelector('[name="bags"]').value,
        //         categories: this.categories.map(cat => document.querySelector(`[value="${cat}"]`).nextElementSibling.innerText),
        //         organization: document.querySelector('[name="organization"]:checked').nextElementSibling.innerText,
        //         address: document.querySelector('[name="address"]').value,
        //         city: document.querySelector('[name="city"]').value,
        //         postcode: document.querySelector('[name="postcode"]').value,
        //         phone: document.querySelector('[name="phone"]').value,
        //         date: document.querySelector('[name="date"]').value,
        //         time: document.querySelector('[name="time"]').value,
        //         more_info: document.querySelector('[name="more_info"]').value
        //     };
        //
        //     document.getElementById('summary-items').innerText = `${formData.bags} worki: ${formData.categories.join(', ')}`;
        //     document.getElementById('summary-organization').innerText = formData.organization;
        //     document.getElementById('summary-address').innerText = formData.address;
        //     document.getElementById('summary-city').innerText = formData.city;
        //     document.getElementById('summary-postcode').innerText = formData.postcode;
        //     document.getElementById('summary-phone').innerText = formData.phone;
        //     document.getElementById('summary-date').innerText = formData.date;
        //     document.getElementById('summary-time').innerText = formData.time;
        //     document.getElementById('summary-more_info').innerText = formData.more_info || 'Brak uwag';
        // }
        populateSummary() {
            // Collect form data and populate summary section
            const bags = document.querySelector('[name="bags"]').value;
            const categories = Array.from(document.querySelectorAll('[name="categories"]:checked'))
                          .map(el => el.parentElement.querySelector('.description').innerText.trim());
            const organization = document.querySelector('[name="organization"]:checked');
            const address = document.querySelector('[name="address"]').value;
            const city = document.querySelector('[name="city"]').value;
            const postcode = document.querySelector('[name="postcode"]').value;
            const phone = document.querySelector('[name="phone"]').value;
            const date = document.querySelector('[name="date"]').value;
            const time = document.querySelector('[name="time"]').value;
            const moreInfo = document.querySelector('[name="more_info"]').value || 'Brak uwag';

            const categoriesText = categories.length > 0 ? categories.join(', ') : 'Brak kategorii wybranych';
            const organizationText = organization ? organization.parentElement.querySelector('.description').innerText : 'Brak organizacji wybranej';

            document.getElementById('summary-items').innerText = `Worki: ${bags}, Kategorie: ${categoriesText}`;
            document.getElementById('summary-organization').innerText = organizationText;
            document.getElementById('summary-address').innerText = address;
            document.getElementById('summary-city').innerText = city;
            document.getElementById('summary-postcode').innerText = postcode;
            document.getElementById('summary-phone').innerText = phone;
            document.getElementById('summary-date').innerText = date;
            document.getElementById('summary-time').innerText = time;
            document.getElementById('summary-more_info').innerText = moreInfo;
            console.log(bags);
            console.log(categories);
            console.log(categoriesText);
            console.log(organization);
            console.log(organizationText)
        }


        submit(e) {
            e.preventDefault();
            // Implement validation if needed

            // Update summary one last time before submission
            this.populateSummary();


            // Proceed with form submission
            this.currentStep++;
            this.updateForm();
        }
    }


    const form = document.querySelector(".form--steps");
    if (form !== null) {
        new FormSteps(form);
    }
});
