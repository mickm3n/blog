// This script adds copy buttons to all pre > code elements
document.addEventListener('DOMContentLoaded', (event) => {
    document.querySelectorAll('pre > code').forEach((codeBlock) => {
        const container = codeBlock.parentNode;
        const copyButton = document.createElement('button');
        copyButton.className = 'copy-code-button';
        copyButton.type = 'button';
        copyButton.innerText = 'Copy';

        copyButton.addEventListener('click', () => {
            navigator.clipboard.writeText(codeBlock.innerText).then(
                () => {
                    copyButton.innerText = 'Copied!';
                    setTimeout(() => {
                        copyButton.innerText = 'Copy';
                    }, 2000);
                },
                (error) => {
                    console.error('Failed to copy code: ', error);
                }
            );
        });

        container.appendChild(copyButton);
    });
});
