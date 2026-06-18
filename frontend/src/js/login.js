import { mostrarToast } from './toast_func.js';

const formEmail = document.getElementById('formEmail');
const formSenha = document.getElementById('formSenha');

document.getElementById('formLogin').addEventListener('submit', async (e) => {
    e.preventDefault();

    const response = await fetch('/logar', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            email: formEmail.value,
            senha: formSenha.value
        })
    });

    const data = await response.json();

    if (response.ok && data.redirect) {
        mostrarToast('Login realizado com sucesso!', 'success');

        setTimeout(() => {
            window.location.href = data.redirect;
        }, 800);
    } else {
        mostrarToast('Credenciais inválidas', 'error');
    }
});