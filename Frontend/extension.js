const vscode = require('vscode');
const path = require('path');
const fs = require('fs');

function activate(context) {
    vscode.window.showInformationMessage('Extensão carregada!');

    let disposable = vscode.commands.registerCommand('helloExtension.openDialog', () => {
        // Cria o painel WebView
        const panel = vscode.window.createWebviewPanel(
            'helloDialog',           // ID interno do painel
            'Hello Dialog',          // Título da aba
            vscode.ViewColumn.Two,   // Onde abrir
            { enableScripts: true }  // Permite JavaScript no WebView
        );

        // Lê o arquivo webview.html e injeta no painel
        const htmlPath = path.join(context.extensionPath, 'webview.html');
        panel.webview.html = fs.readFileSync(htmlPath, 'utf8');

        // Recebe mensagens enviadas pelo botão dentro do WebView
        panel.webview.onDidReceiveMessage(
            message => {
                vscode.window.showInformationMessage(`Você digitou: ${message.text}`);
            },
            undefined,
            context.subscriptions
        );
    });

    context.subscriptions.push(disposable);
}

function deactivate() {}

module.exports = { activate, deactivate };
