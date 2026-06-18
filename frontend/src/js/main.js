function login(){
  setTimeout(() => {window.location.href = "/login";}, 800);
}

function register(){
  setTimeout(() => {window.location.href = "/register";}, 800);
}

function scrollToFeatures(){
  document.getElementById("features").scrollIntoView({
    behavior: "smooth"
  });
}