document.addEventListener('DOMContentLoaded', (event) => {
    document.querySelectorAll('pre.z-code').forEach((preBlock) => {
        const copyButton = document.createElement('button');
        copyButton.className = 'copy-code-button';
        copyButton.type = 'button';
        copyButton.innerText = 'Copy';

        preBlock.appendChild(copyButton);

        copyButton.addEventListener('click', () => {
            const codeBlock = preBlock.querySelector('code');
            const codeText = codeBlock.innerText;

            navigator.clipboard.writeText(codeText).then(
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
    });
});
