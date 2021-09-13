const containers = Array.from(document.getElementsByClassName('imgcontainer'));
const modal = document.getElementById('modal-plain');
const modalImg = document.getElementById('modal-img');
const closeButton = document.getElementById('close-button');

containers.forEach(container => {
    container.onclick = (e) => {
        modal.style.display = 'block';
        modalImg.src = e.target.src;
    };
});

closeButton.onclick = () => {
    modal.style.display = 'none';
}

modal.onclick = (e) => {
    if (e.target === modalImg) {
        return;
    }
    modal.style.display = 'none';
}   