export function mostrarToast(mensagem, tipo = 'success') {
    const toastEl = document.getElementById('toastFeedback');
    const toastMessage = document.getElementById('toastMessage');

    toastMessage.textContent = mensagem;

    toastEl.classList.remove('bg-success', 'bg-danger', 'bg-primary');
    toastEl.classList.add(tipo === 'success' ? 'bg-success' : tipo === 'error' ? 'bg-danger' : 'bg-primary');

    const toast = new bootstrap.Toast(toastEl);
    toast.show();
}