const navbar = document.getElementById("mobile-navbar");
const main = document.getElementById("question-main");
let lastScrollTop = 0;
main.addEventListener("scroll", () => {
	let scrollTop = main.scrollTop;
	if (scrollTop > lastScrollTop) {
		navbar.style.top = "-10vh"; // 上滑隐藏
	} else {
		navbar.style.top = "0"; // 下滑显示
	}
	lastScrollTop = scrollTop;
});

// 抽屉开关逻辑
const drawerBank = document.getElementById("drawer-bank");
const drawerNav = document.getElementById("drawer-nav");

document.getElementById("toggle-bank").addEventListener("click", function () {
	drawerBank.classList.toggle("open");
	drawerNav.classList.remove("open"); // 只允许一个抽屉打开
});

document.getElementById("toggle-nav").addEventListener("click", function () {
	drawerNav.classList.toggle("open");
	drawerBank.classList.remove("open"); // 只允许一个抽屉打开
});

// 点击空白区域关闭抽屉（可选）
document.addEventListener("click", function (event) {
	if (
		!drawerBank.contains(event.target) &&
		!event.target.closest("#toggle-bank")
	) {
		drawerBank.classList.remove("open");
	}
	if (
		!drawerNav.contains(event.target) &&
		!event.target.closest("#toggle-nav")
	) {
		drawerNav.classList.remove("open");
	}
});

document.addEventListener("DOMContentLoaded", function () {
	let timers = {};
	document
		.querySelectorAll(".options input[type='radio']")
		.forEach((input) => {
			input.addEventListener("change", function () {
				let questionId = this.name.match(/\d+/)[0];
				let selectedValue = this.value;
				let correctAnswer = this.closest(".question").dataset.correct; // 正确答案（通过 Thymeleaf 绑定）
				console.log(selectedValue, "///", correctAnswer);
				let feedbackDiv = document.getElementById(
					"feedback-" + questionId
				);
				let navButton = document.getElementById(
					"nav-question-" + questionId
				);
				let navmobButton = document.getElementById(
					"nav-question-mob-" + questionId
				);
				if (timers[questionId]) clearTimeout(timers[questionId]);
				timers[questionId] = setTimeout(function () {
					if (selectedValue === correctAnswer) {
						feedbackDiv.textContent = "回答正确！";
						feedbackDiv.style.color = "green";
						navButton.style.backgroundColor = "green";
						navButton.style.color = "white";
						navmobButton.style.backgroundColor = "green";
						navmobButton.style.color = "white";
					} else {
						feedbackDiv.textContent = "回答错误";
						feedbackDiv.style.color = "red";
						navButton.style.backgroundColor = "red";
						navButton.style.color = "white";
						navmobButton.style.backgroundColor = "red";
						navmobButton.style.color = "white";
					}
				}, 1000); //默认三秒判题
			});
		});
});
