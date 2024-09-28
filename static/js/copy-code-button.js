document.addEventListener('DOMContentLoaded', (event) => {
    document.querySelectorAll('pre.z-code').forEach((preBlock) => {
        const copyButton = document.createElement('button');
        copyButton.className = 'copy-code-button';
        copyButton.type = 'button';
        copyButton.innerText = 'Copy';
        copyButton.style.display = 'none';

        document.body.appendChild(copyButton);

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

        const updateButtonPosition = () => {
            const rect = preBlock.getBoundingClientRect();
            if (rect.top < window.innerHeight && rect.bottom > 0) {
                copyButton.style.display = 'block';
                copyButton.style.top = `${Math.max(rect.top, 0)}px`;
                copyButton.style.right = `${window.innerWidth - rect.right + 5}px`;
            } else {
                copyButton.style.display = 'none';
            }
        };

        window.addEventListener('scroll', updateButtonPosition);
        window.addEventListener('resize', updateButtonPosition);

        updateButtonPosition();
    });
});
