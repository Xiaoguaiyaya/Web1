document.addEventListener('DOMContentLoaded', function () {
    const navList = document.querySelector('.nav-list');
    const navContainer0 = navList.querySelectorAll('.dropdown-container-0');

    for (var i = 0; i < navContainer0.length; i++) {
        const dropdownList0 = navContainer0[i].querySelector('.dropdown-list-0');

        let timeoutId0; // 用于延迟隐藏下拉列表

        navContainer0[i].addEventListener('mouseenter', () => {
            clearTimeout(timeoutId0); // 清除延迟隐藏的计时器
            dropdownList0.style.display = 'block';
            dropdownList0.style.animation = 'expandDropdown 0.3s ease-in-out'; // 添加展开动画
        });

        navContainer0[i].addEventListener('mouseleave', () => {
            timeoutId0 = setTimeout(() => {
                dropdownList0.style.animation = 'collapseDropdown 0.3s ease-in-out';
                dropdownList0.style.display = 'none';
            }, 100); // 设置0.5秒延迟
        });

        dropdownList0.addEventListener('mouseenter', () => {
            clearTimeout(timeoutId0); // 清除延迟隐藏的计时器
        });

        dropdownList0.addEventListener('mouseleave', () => {
            timeoutId0 = setTimeout(() => {
                dropdownList0.style.animation = 'collapseDropdown 0.3s ease-in-out';
                dropdownList0.style.display = 'none';
            }, 100); // 设置0.5秒延迟
        });
    }
});
