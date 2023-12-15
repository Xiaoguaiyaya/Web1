const navContainer = document.querySelector('.nav-1-2');
const dropdownList = navContainer.querySelector('.dropdown-list');

let timeoutId; // 用于延迟隐藏下拉列表

navContainer.addEventListener('mouseenter', () => {
    clearTimeout(timeoutId); // 清除延迟隐藏的计时器
    dropdownList.style.display = 'block';
    dropdownList.style.animation = 'expandDropdown 0.3s ease-in-out'; // 添加展开动画
});

navContainer.addEventListener('mouseleave', () => {
    timeoutId = setTimeout(() => {
        dropdownList.style.animation = 'collapseDropdown 0.3s ease-in-out';
        dropdownList.style.display = 'none';
    }, 300); // 设置0.5秒延迟
});

dropdownList.addEventListener('mouseenter', () => {
    clearTimeout(timeoutId); // 清除延迟隐藏的计时器
});

dropdownList.addEventListener('mouseleave', () => {
    timeoutId = setTimeout(() => {
        dropdownList.style.animation = 'collapseDropdown 0.3s ease-in-out';
        dropdownList.style.display = 'none';
    }, 300); // 设置0.5秒延迟
});