import { mostrarToast } from './toast_func.js';

const formNome = document.getElementById('formNome');
const formEmail = document.getElementById('formEmail');
const formSenha = document.getElementById('formSenha');
const formCSenha = document.getElementById('formSenhaConfirm');

document.getElementById('formRegistro').addEventListener('submit', async (e) => {
    e.preventDefault();

    if (formSenha.value !== formCSenha.value) {
        mostrarToast('As senhas não coincidem', 'error');
        return;
    }

    const response = await fetch('/registro', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            nome: formNome.value,
            email: formEmail.value,
            senha: formSenha.value
        })
    });

    const data = await response.json();

    if (response.ok && data.redirect) {
        mostrarToast('Registro realizado com sucesso!', 'success');

        setTimeout(() => {
            window.location.href = data.redirect;
        }, 800);
    } else {
        mostrarToast('Credenciais inválidas', 'error');
    }
});