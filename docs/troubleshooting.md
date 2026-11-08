# Troubleshooting: falhas reais, causa e solução

Registro dos problemas encontrados ao montar este pipeline com um GitLab Runner no Windows. Cada item tem o sintoma, a causa real e o que resolveu.

## 1. Job pendente (stuck)

- **Sintoma:** o job fica como "Pendente" e o painel diz que não há runner online compatível.
- **Causa:** o runner estava online, mas não estava atribuído ao projeto. Além disso, um job com tag só roda em runner que tenha exatamente aquela tag, e um runner marcado como *Protected* só pega branches protegidas.
- **Solução:** habilitar o runner no projeto (Settings, CI/CD, Runners), conferir a tag `lab-local`, deixar *Protected* desmarcado e disparar um pipeline novo (`git commit --allow-empty -m "novo pipeline"` e `git push`).

## 2. `exec: "pwsh": executable file not found in %PATH%`

- **Sintoma:** `Job failed (system failure)` logo na preparação do ambiente.
- **Causa:** o runner escolheu o PowerShell Core (`pwsh`) como shell, e ele não está instalado. O Windows traz o Windows PowerShell (`powershell`).
- **Solução:** no `config.toml`, `shell = "powershell"`, e reiniciar o serviço.

## 3. `docker : O termo 'docker' não é reconhecido`

- **Sintoma:** o passo `docker-compose build` falha, embora o mesmo comando funcione no terminal do usuário.
- **Causa:** o serviço do runner roda como conta de sistema (LocalSystem). O Docker Desktop foi instalado só para o usuário (pasta `AppData`), então o `PATH` do usuário não vale para o serviço.
- **Solução:** definir `environment` no `config.toml` com o `PATH` incluindo a pasta do `docker.exe`. Para achá-la: `Get-Command docker | Select-Object -ExpandProperty Source`.

## 4. `docker: unknown command: docker compose` e aviso do buildx

- **Sintoma:** `unknown command: docker compose`; depois, `buildx Docker CLI plugin not found: falling back to the classic builder`.
- **Causa:** `docker compose` (com espaço) é um plugin do CLI, e os plugins ficam numa pasta que o runner não enxergava. `docker-compose` (com hífen) é um executável independente, que estava na pasta incluída no `PATH`. O aviso do buildx tem a mesma origem e é inofensivo aqui: o build usa o construtor clássico.
- **Solução:** usar `docker-compose` no `.gitlab-ci.yml`.

## 5. `powershell` não reconhecido depois de ajustar o PATH

- **Sintoma:** o passo que chama `aguardar_saude.ps1` falha com `powershell` não reconhecido, e depois também com `powershell.exe`.
- **Causa:** a variável `environment` do `config.toml` **substitui** o `PATH` do job, não soma. E o `powershell.exe` não fica direto em `System32`: fica em `System32\WindowsPowerShell\v1.0`, subpasta que não estava no `PATH`.
- **Solução:** caminho absoluto no `.gitlab-ci.yml` (ou incluir a pasta `v1.0` no `PATH` do `config.toml`).

## 6. YAML inválido por traço duplicado

- **Sintoma:** pipeline recusado ou comando ignorado.
- **Causa:** `- - comando` cria uma lista dentro de outra lista.
- **Solução:** um traço por comando. O editor de pipeline do GitLab valida a sintaxe antes do commit.

## 7. `flag provided but not defined: -all-services`

- **Sintoma:** erro ao tentar limpar registros do runner.
- **Causa:** a flag não existe. A correta é `--all-runners`.
- **Solução:** `.\gitlab-runner.exe unregister --help` lista as opções. A mensagem `service is not installed` era normal quando o serviço ainda não tinha sido instalado.

## 8. `New-NetFirewallRule : Acesso negado`

- **Causa:** alterar o firewall exige privilégios de administrador.
- **Solução:** abrir o PowerShell como Administrador.

## 9. Ping responde, mas a porta não abre

- **Sintoma:** a rede privada (VPN) respondia ao `ping`, e o navegador não conseguia abrir a porta.
- **Causa:** a publicação da porta no compose estava presa em `127.0.0.1`, o que só aceita conexões do próprio computador.
- **Solução:** publicar em outra interface exige uma decisão de segurança. Mudar para `0.0.0.0` abre a porta para toda a rede local, além da VPN. Alternativas mais seguras: prender a porta ao IP da VPN ou manter `127.0.0.1` e publicar com `tailscale serve`.
- **Lição:** `ping` prova a rede, não a porta. Teste cada camada: `Test-NetConnection IP -Port 8080`.

## Método de diagnóstico

1. Copie a primeira linha de erro, exatamente como aparece.
2. Pergunte: onde isso roda (PC, runner ou contêiner)? Com qual usuário (o seu ou a conta de sistema)? Com qual `PATH`?
3. Reproduza à mão o comando que falhou.
4. Separe as camadas, de dentro para fora: código, imagem, contêiner, rede do Docker, firewall, VPN.
5. Mude uma coisa por vez, com commits pequenos.
