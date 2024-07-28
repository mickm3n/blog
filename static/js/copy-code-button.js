document.addEventListener('DOMContentLoaded', (event) => {
    document.querySelectorAll('pre > code').forEach((codeBlock) => {
        const container = codeBlock.parentNode;
        const copyButton = document.createElement('button');
        copyButton.className = 'copy-code-button';
        copyButton.type = 'button';
        copyButton.innerText = 'Copy';

        copyButton.addEventListener('click', () => {
            // Get all the table rows
            const rows = codeBlock.querySelectorAll('table tr');
            // Extract only the text content from each row, ignoring the line numbers
            const codeText = Array.from(rows)
                .map(row => {
                    const codePart = row.querySelector('td:nth-child(2)');
                    return codePart ? codePart.textContent : '';
                })
                .join('');

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

        container.appendChild(copyButton);
    });
});
