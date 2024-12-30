document.addEventListener("DOMContentLoaded", () => {
  const addSearchFunctionality = (inputId, listId) => {
    const input = document.querySelector(`#${inputId}`);
    const list = document.querySelector(`#${listId}`);
    const listItems = list.querySelectorAll("li");

    const onSearch = () => {
      const filter = input.value.toUpperCase();
      listItems.forEach((item) => {
        const text = item.textContent || item.innerText;
        item.style.display = text.toUpperCase().includes(filter) ? "" : "none";
      });
    };

    input.addEventListener("focus", () => {
      list.classList.remove("hidden");
    });

    input.addEventListener("blur", () => {
      setTimeout(() => list.classList.add("hidden"), 100); // Add delay to allow click event to register
    });

    listItems.forEach((item) => {
      item.addEventListener("click", () => {
        input.value = item.textContent || item.innerText;
        list.classList.add("hidden");
      });
    });

    input.addEventListener("keyup", onSearch);
  };

  // Add functionality for both State and District search
  addSearchFunctionality("state-search", "state-list");
  addSearchFunctionality("district-search", "district-list");
});
