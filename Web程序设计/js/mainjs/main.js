let slideIndex = 0;
const slides = document.getElementsByClassName("slide");

function showSlides() {
    for (let i = 0; i < slides.length; i++) {
        slides[i].style.display = "none";
    }
    slides[slideIndex].style.display = "block";
}

function plusSlides(n) {
    slideIndex += n;
    if (slideIndex < 0) {
        slideIndex = slides.length - 1;
    } else if (slideIndex >= slides.length) {
        slideIndex = 0;
    }
    showSlides();
}

showSlides(); // 初始显示第一张幻灯片

const prevButtons = document.querySelectorAll(".prev");
const nextButtons = document.querySelectorAll(".next");

for (let i = 0; i < prevButtons.length; i++) {
    prevButtons[i].addEventListener("click", () => plusSlides(-1));
}

for (let i = 0; i < nextButtons.length; i++) {
    nextButtons[i].addEventListener("click", () => plusSlides(1));
}

setInterval(() => plusSlides(1), 3000); // 自动播放
