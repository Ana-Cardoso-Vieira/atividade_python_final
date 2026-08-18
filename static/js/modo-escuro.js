(function () {
  const CHAVE = "painel-tarefas-modo-escuro";
  const body = document.body;
  const botao = document.getElementById("btnModoEscuro");

  function aplicarModo(ativo) {
    body.classList.toggle("modo-escuro", ativo);
    if (botao) {
      botao.innerHTML = ativo
        ? '<i class="bi bi-sun"></i>'
        : '<i class="bi bi-moon-stars"></i>';
    }
  }

  const salvo = localStorage.getItem(CHAVE) === "true";
  aplicarModo(salvo);

  if (botao) {
    botao.addEventListener("click", function () {
      const novoEstado = !body.classList.contains("modo-escuro");
      aplicarModo(novoEstado);
      localStorage.setItem(CHAVE, novoEstado);
    });
  }
})();
