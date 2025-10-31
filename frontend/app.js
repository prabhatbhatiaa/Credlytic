const ADMIN_WALLET_ADDRESS = "0xf8c16a7ea7e2ebb554ee7d44996d11a5255fb22fa111cfdc2bb886d3d7b1952e";
const BACKEND_MINT_URL = "http://127.0.0.1:5000/create-cert";
const BACKEND_FIND_URL = "http://127.0.0.1:5000/get-my-certs";

let connectedAccount = null;
let isAdmin = false;
let availableWallets = [];

let walletSection, connectButtonsDiv, walletInfoDiv, connectedAddressSpan,
    connectedWalletNameSpan, disconnectBtn, adminSection, studentNameInput,
    courseNameInput, studentIdInput, mintBtn, studentSection,
    studentIdentifierSpan, findCertsBtn, studentResultsDiv, resultArea;

function logResult(htmlContent, isError = false) {
    if (!resultArea) {
        console.error("Result area not found!");
        return;
    }
    
    console.log("Result Update:", String(htmlContent).replace(/<[^>]*>?/gm, ''));
    resultArea.innerHTML = htmlContent;
    resultArea.style.color = isError ? '#dc2626' : '#15803d';
    resultArea.style.backgroundColor = isError ? '#fee2e2' : '#dcfce7';
    resultArea.style.borderColor = isError ? '#f87171' : '#86efac';
}

function setLoading(buttonElement, isLoading, loadingText = "Processing...", originalText = "Submit") {
    if (!buttonElement) return;
    
    buttonElement.disabled = isLoading;
    
    if (!buttonElement.dataset.originalText && isLoading) {
        buttonElement.dataset.originalText = buttonElement.textContent;
    }
    
    if (!isLoading && !buttonElement.dataset.originalText) {
        if (buttonElement.id === 'mintBtn') {
            originalText = 'Issue Certificate (Mint NFT)';
        } else if (buttonElement.id === 'findCertsBtn') {
            originalText = 'Find My Certificates';
        } else {
            originalText = buttonElement.textContent;
        }
    }
    
    buttonElement.textContent = isLoading ? loadingText : buttonElement.dataset.originalText || originalText;
    
    if (!isLoading) {
        delete buttonElement.dataset.originalText;
    }
}

async function detectWallets() {
    console.log("Starting wallet detection...");
    availableWallets = [];
    logResult('Detecting wallets...');
    connectButtonsDiv.innerHTML = '<p class="placeholder">Checking...</p>';
    
    if (window.aptos) {
        console.log("Petra detected.");
        availableWallets.push({
            name: 'Petra',
            icon: 'https://petra.app/favicon.ico',
            connect: async () => window.aptos.connect(),
            disconnect: async () => window.aptos.disconnect(),
            network: typeof window.aptos.network === 'function' ? async () => window.aptos.network() : undefined,
            signAndSubmitTransaction: typeof window.aptos.signAndSubmitTransaction === 'function' 
                ? async (p) => window.aptos.signAndSubmitTransaction(p) 
                : undefined,
            isConnected: typeof window.aptos.isConnected === 'function' 
                ? async () => await window.aptos.isConnected() 
                : undefined,
        });
    } else {
        console.log("Petra not detected.");
    }
    
    if (window.AptosConnectWalletAdapter && window.AptosConnectWalletAdapter.AptosConnectWallet) {
        console.log("AptosConnect script loaded.");
        
        try {
            const aptosConnect = new window.AptosConnectWalletAdapter.AptosConnectWallet({
                network: 'devnet'
            });
            
            if (aptosConnect && aptosConnect.name && aptosConnect.icon && 
                typeof aptosConnect.connect === 'function' && 
                typeof aptosConnect.disconnect === 'function' && 
                typeof aptosConnect.account === 'function' && 
                typeof aptosConnect.signAndSubmitTransaction === 'function') {
                
                console.log("Aptos Connect instance valid.");
                availableWallets.push({
                    name: aptosConnect.name,
                    icon: aptosConnect.icon,
                    connect: async () => aptosConnect.connect(),
                    disconnect: async () => aptosConnect.disconnect(),
                    network: typeof aptosConnect.network === 'function' 
                        ? async () => aptosConnect.network() 
                        : undefined,
                    signAndSubmitTransaction: async (payload) => aptosConnect.signAndSubmitTransaction(payload),
                    account: async () => aptosConnect.account(),
                    isConnected: async () => {
                        try {
                            const account = await aptosConnect.account();
                            return !!account?.address;
                        } catch {
                            return false;
                        }
                    }
                });
            } else {
                console.warn("Aptos Connect instance incomplete.");
            }
        } catch (e) {
            console.error("Error initializing Aptos Connect:", e);
        }
    } else {
        console.log("AptosConnect script not detected.");
    }
    
    console.log("Detection finished. Found:", availableWallets.length);
    renderConnectButtons();
}

function renderConnectButtons() {
    if (!connectButtonsDiv) return;
    
    connectButtonsDiv.innerHTML = '';
    
    if (availableWallets.length === 0) {
        connectButtonsDiv.innerHTML = '<p class="placeholder">No wallets found.</p>';
        if (!connectedAccount) {
            logResult('No wallets found.', true);
        }
    } else {
        availableWallets.forEach(wallet => {
            const button = document.createElement('button');
            button.setAttribute('type', 'button');
            button.onclick = () => handleConnect(wallet.name);
            
            const buttonText = `Connect ${wallet.name}`;
            button.dataset.originalText = buttonText;
            button.innerHTML = `${wallet.icon ? `<img src="${wallet.icon}" alt="${wallet.name} logo">` : ''} ${buttonText}`;
            
            connectButtonsDiv.appendChild(button);
        });
        
        if (!connectedAccount) {
            logResult('Please connect wallet.');
        }
    }
}

async function handleConnect(walletName) {
    const wallet = availableWallets.find(w => w.name === walletName);
    
    if (!wallet || typeof wallet.connect !== 'function') {
        logResult(`Cannot connect ${walletName}.`, true);
        return;
    }
    
    logResult(`Connecting ${walletName}...`);
    
    const button = Array.from(connectButtonsDiv?.querySelectorAll('button') || [])
        .find(b => b.textContent.includes(walletName));
    
    setLoading(button, true, 'Connecting...');
    
    try {
        const response = await wallet.connect();
        let address = response?.address;
        
        if (!address && typeof wallet.account === 'function') {
            const accountInfo = await wallet.account();
            address = accountInfo?.address;
        }
        
        if (address) {
            connectedAccount = {
                address: address,
                name: walletName,
                walletInstance: wallet
            };
            
            console.log("Comparing:", address?.toLowerCase(), ADMIN_WALLET_ADDRESS.toLowerCase());
            isAdmin = address?.toLowerCase() === ADMIN_WALLET_ADDRESS.toLowerCase();
            console.log("Connected:", connectedAccount, "Is Admin:", isAdmin);
            
            updateUI();
        } else {
            throw new Error("Address not provided.");
        }
    } catch (e) {
        console.error(`Error connecting ${walletName}:`, e);
        logResult(`Failed to connect ${walletName}. ${e.message || ''}`, true);
        connectedAccount = null;
        isAdmin = false;
        updateUI();
    } finally {
        setLoading(button, false);
    }
}

async function handleDisconnect() {
    if (!connectedAccount?.walletInstance?.disconnect) {
        console.warn("Disconnect failed.");
        connectedAccount = null;
        isAdmin = false;
        updateUI();
        return;
    }
    
    logResult('Disconnecting...');
    
    try {
        await connectedAccount.walletInstance.disconnect();
        console.log("Disconnected.");
    } catch (e) {
        console.error("Disconnect error:", e);
    } finally {
        connectedAccount = null;
        isAdmin = false;
        updateUI();
    }
}

function updateUI() {
    if (!walletInfoDiv || !connectButtonsDiv || !adminSection || !studentSection || 
        !connectedAddressSpan || !connectedWalletNameSpan || !studentIdentifierSpan) {
        console.error("UI Update failed: elements missing.");
        return;
    }
    
    if (connectedAccount) {
        connectedAddressSpan.textContent = `${connectedAccount.address.slice(0, 6)}...${connectedAccount.address.slice(-4)}`;
        connectedWalletNameSpan.textContent = connectedAccount.name;
        walletInfoDiv.style.display = 'flex';
        connectButtonsDiv.style.display = 'none';
        
        if (isAdmin) {
            adminSection.style.display = 'block';
            studentSection.style.display = 'none';
            logResult('<p>Admin wallet connected. Ready to issue certificates.</p>');
        } else {
            adminSection.style.display = 'none';
            studentSection.style.display = 'block';
            studentIdentifierSpan.textContent = connectedAccount.address;
            studentResultsDiv.innerHTML = '<p class="placeholder">Click button to search for your records.</p>';
            logResult('<p>Student wallet connected. You can now search for your records.</p>');
        }
    } else {
        walletInfoDiv.style.display = 'none';
        connectButtonsDiv.style.display = 'block';
        adminSection.style.display = 'none';
        studentSection.style.display = 'none';
        renderConnectButtons();
        logResult('<p>Please connect wallet.</p>');
    }
}

async function handleMint(event) {
    if (event) event.preventDefault();
    console.log("Mint button clicked! preventDefault called.");
    
    if (!mintBtn) {
        console.error("Mint button not found!");
        return;
    }
    
    if (!isAdmin || !connectedAccount) {
        logResult('Error: Admin not connected.', true);
        return;
    }
    
    const name = studentNameInput?.value?.trim();
    const course = courseNameInput?.value?.trim();
    const studentId = studentIdInput?.value?.trim();
    
    if (!name || !course || !studentId) {
        logResult('Error: Please fill in all Admin form fields.', true);
        return;
    }
    
    const aptosAddressRegex = /^0x[0-9a-fA-F]{64,66}$/;
    if (!aptosAddressRegex.test(studentId)) {
        logResult('Error: Student Identifier must be a valid Aptos wallet address (e.g., 0x...).', true);
        return;
    }
    
    logResult('<p>Issuing certificate... Contacting backend...</p>');
    setLoading(mintBtn, true, 'Issuing...');
    
    let success = false;
    let resultData = null;
    
    try {
        const response = await fetch(BACKEND_MINT_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                name: name,
                course: course,
                student_id: studentId
            }),
        });
        
        resultData = await response.json();
        
        if (!response.ok) {
            throw new Error(resultData.error || `HTTP error! Status: ${response.status}`);
        }
        
        if (!resultData.success) {
            throw new Error(resultData.error || 'Unknown backend error.');
        }
        
        success = true;
    } catch (error) {
        console.error("Minting Fetch Error:", error);
        logResult(`<h3>Minting Error:</h3><p>${error.message}</p>`, true);
    } finally {
        setLoading(mintBtn, false, '', 'Issue Certificate (Mint NFT)');
        console.log("Fetch finished. Success:", success);
        
        if (success && resultData) {
            let successMsg = `<h3>Success! Certificate Issued!</h3>`;
            successMsg += `<p class="break-all">Tx Hash: ${resultData.tx_hash}</p>`;
            successMsg += `<a href="${resultData.explorer_url}" target="_blank" rel="noopener noreferrer">View on Aptos Explorer (Verifier Link)</a>`;
            
            if (resultData.download_url) {
                successMsg += `<a href="${resultData.download_url}">Download Certificate PNG</a>`;
            } else {
                successMsg += `<p style="color: orange;">${resultData.message || 'PNG failed.'}</p>`;
            }
            
            logResult(successMsg);
            
            if (studentNameInput) studentNameInput.value = '';
            if (courseNameInput) courseNameInput.value = '';
            if (studentIdInput) studentIdInput.value = '';
        } else if (!success && resultData) {
            logResult(`<h3>Minting Error:</h3><p>${resultData.error || 'Unknown error.'}</p>`, true);
        }
    }
}

async function findMyCertificates(event) {
    if (event) event.preventDefault();
    console.log("Find Certs button clicked! preventDefault called.");
    
    if (!findCertsBtn) {
        console.error("Find Certs button not found!");
        return;
    }
    
    if (!connectedAccount) {
        if (studentResultsDiv) {
            studentResultsDiv.innerHTML = '<p style="color: red;">Error: Wallet not connected.</p>';
        }
        return;
    }
    
    const searchId = connectedAccount.address;
    
    if (studentResultsDiv) {
        studentResultsDiv.innerHTML = '<p class="placeholder">Searching for your records...</p>';
    }
    
    setLoading(findCertsBtn, true, 'Searching...');
    
    let success = false;
    let resultData = null;
    
    try {
        const response = await fetch(BACKEND_FIND_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ student_id: searchId }),
        });
        
        resultData = await response.json();
        
        if (!response.ok) {
            throw new Error(resultData.error || `HTTP error! status: ${response.status}`);
        }
        
        success = true;
    } catch (error) {
        console.error("Error fetching certificates:", error);
        if (studentResultsDiv) {
            studentResultsDiv.innerHTML = `<p style="color: red;">Connection Error: ${error.message}</p>`;
        }
    } finally {
        setLoading(findCertsBtn, false, '', 'Find My Certificates');
        
        if (success && resultData && studentResultsDiv) {
            if (resultData.error) {
                studentResultsDiv.innerHTML = `<p style="color: red;">Error: ${resultData.error}</p>`;
            } else if (resultData.certificates && resultData.certificates.length > 0) {
                let certHtml = '<h3>Your Certificates:</h3><ul>';
                
                resultData.certificates.forEach(cert => {
                    certHtml += `
                        <li style="margin-bottom: 10px;">
                            <strong>${cert.name}</strong><br>
                            <a href="${cert.explorer_url}" target="_blank" rel="noopener noreferrer">[View on Explorer]</a>
                            <a href="${cert.download_url}" target="_blank" rel="noopener noreferrer" style="margin-left: 10px;">[Download PNG]</a>
                        </li>`;
                });
                
                certHtml += '</ul>';
                studentResultsDiv.innerHTML = certHtml;
            } else if (resultData.certificates) {
                studentResultsDiv.innerHTML = '<p class="placeholder">No certificates were found for your wallet address.</p>';
            } else {
                studentResultsDiv.innerHTML = `<p style="color: red;">Error: Could not parse certificate data.</p>`;
            }
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    console.log("DOM fully loaded. Grabbing elements and attaching listeners...");
    
    walletSection = document.getElementById('walletSection');
    connectButtonsDiv = document.getElementById('connectButtons');
    walletInfoDiv = document.getElementById('walletInfo');
    connectedAddressSpan = document.getElementById('connectedAddress');
    connectedWalletNameSpan = document.getElementById('connectedWalletName');
    disconnectBtn = document.getElementById('disconnectBtn');
    adminSection = document.getElementById('adminSection');
    studentNameInput = document.getElementById('studentName');
    courseNameInput = document.getElementById('courseName');
    studentIdInput = document.getElementById('studentId');
    mintBtn = document.getElementById('mintBtn');
    studentSection = document.getElementById('studentSection');
    studentIdentifierSpan = document.getElementById('studentIdentifier');
    findCertsBtn = document.getElementById('findCertsBtn');
    studentResultsDiv = document.getElementById('studentResults');
    resultArea = document.getElementById('resultArea');
    
    if (disconnectBtn) {
        disconnectBtn.addEventListener('click', handleDisconnect);
        console.log("Disconnect listener attached.");
    } else {
        console.error("Disconnect button not found!");
    }
    
    if (mintBtn) {
        mintBtn.addEventListener('click', (event) => handleMint(event));
        console.log("Mint listener attached.");
    } else {
        console.error("Mint button not found!");
    }
    
    if (findCertsBtn) {
        findCertsBtn.addEventListener('click', (event) => findMyCertificates(event));
        console.log("Find Certs listener attached.");
    } else {
        console.error("Find Certs button not found!");
    }
    
    detectWallets();
});