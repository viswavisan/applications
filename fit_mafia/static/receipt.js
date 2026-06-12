    function saveAsPDF() {
        const element = document.getElementById('receipt');
        const opt = {
            margin:       10,
            filename:     'receipt_{{ txn.transaction_id }}.pdf',
            image:        { type: 'jpeg', quality: 0.98 },
            html2canvas:  { scale: 2 },
            jsPDF:        { unit: 'mm', format: 'a4', orientation: 'portrait' }
        };
        // Generate and save the PDF
        html2pdf().set(opt).from(element).save();
    }

    function sendReceipt() {
        alert("Send functionality can be integrated with Email or WhatsApp API.");
    }