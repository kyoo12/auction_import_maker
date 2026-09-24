const dropzone = document.getElementById('dropzone');
        const fileInput = document.getElementById('file-input');
        const animContainer = document.getElementById('animation-container');
        const successBox = document.getElementById('success-box');
        const successFilename = document.getElementById('success-filename');
        const dlButton = document.getElementById('dl-button');
        const resetLink = document.getElementById('reset-link');
        const tomHeadImg = document.getElementById('tom-head-img');
        const tomBubble = document.getElementById('tom-speech-bubble');
        const animLabel = document.getElementById('anim-label');
        const iconTemplate = document.getElementById('icon-template');
        const iconDump = document.getElementById('icon-dump');
        const iconOutput = document.getElementById('icon-output');
        const errorToast = document.getElementById('error-toast');

        let rawExcelData = null;
        let outputFileName = '';
        let originalFileName = '';
        let auctionSchema = null;

        // Fetch schema on load
        fetch('schema.json')
            .then(res => res.json())
            .then(data => { auctionSchema = data; })
            .catch(err => console.error("Failed to load schema.json:", err));

        // Prevent browser opening dropped files
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            window.addEventListener(eventName, e => e.preventDefault());
        });

        // Highlights dropzone on hover
        ['dragenter', 'dragover'].forEach(eventName => {
            dropzone.addEventListener(eventName, () => dropzone.classList.add('dragover'));
        });
        ['dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, () => dropzone.classList.remove('dragover'));
        });

        // Click on dropzone triggers hidden file input
        dropzone.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', e => handleFiles(e.target.files));
        dropzone.addEventListener('drop', e => handleFiles(e.dataTransfer.files));

        function showToast(msg) {
            errorToast.textContent = msg;
            errorToast.classList.add('show');
            setTimeout(() => errorToast.classList.remove('show'), 5000);
        }

        function handleFiles(files) {
            if (!files || files.length === 0) return;
            const file = files[0];
            if (!file.name.endsWith('.xlsx')) {
                showToast("Oops! Only .xlsx Excel files are supported.");
                return;
            }

            originalFileName = file.name;
            const baseName = file.name.substring(0, file.name.lastIndexOf('.')) || file.name;
            outputFileName = `lot_import_${baseName}.xlsx`;

            const reader = new FileReader();
            reader.onload = function(e) {
                try {
                    const data = new Uint8Array(e.target.result);
                    const workbook = XLSX.read(data, {type: 'array'});
                    
                    if (!workbook.SheetNames.includes('Lots')) {
                        showToast("Invalid sheet: The Excel file must contain a sheet named exactly 'Lots'.");
                        return;
                    }

                    // Store raw data to process during animation collision
                    rawExcelData = workbook;
                    startChompingAnimation();
                } catch (err) {
                    showToast("Failed to read the Excel file. Make sure it is not corrupted.");
                    console.error(err);
                }
            };
            reader.readAsArrayBuffer(file);
        }

        // Animated chomping logic
        function startChompingAnimation() {
            // Setup views
            dropzone.style.display = 'none';
            animContainer.style.display = 'block';
            successBox.style.display = 'none';
            
            // Reset anim state
            animLabel.textContent = "Eating files...";
            animLabel.style.color = 'var(--text-color)';
            iconTemplate.style.opacity = '1';
            iconTemplate.style.transform = 'scale(1)';
            iconDump.style.opacity = '1';
            iconDump.style.transform = 'scale(1)';
            iconOutput.style.display = 'none';
            
            const duration = 9000; // Exactly 9 seconds
            const startX = -140;
            const finalX = 540;
            let startTime = null;
            let processingDone = false;
            let outputBlob = null;
            let hasErrored = false;
            let lastBiteIndex = -1;

            // Professional cubic ease-in-out function
            function easeInOutCubic(t) {
                return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
            }

            function animate(timestamp) {
                if (!startTime) startTime = timestamp;
                const elapsed = timestamp - startTime;
                const rawProgress = Math.min(elapsed / duration, 1);
                
                // Apply professional cubic easing for smooth start and slow-down finish
                const easedProgress = easeInOutCubic(rawProgress);

                // Calculate exact position based on elapsed eased time
                const tomX = startX + (finalX - startX) * easedProgress;
                tomHeadImg.style.left = tomX + 'px';
                
                // Position speech bubble centered right above his 64px head
                tomBubble.style.left = (tomX - 10) + 'px';
                
                // Energetic mouth biting: toggle every 180ms for a lively, active eating effect
                const toggleInterval = 180;
                const biteIndex = Math.floor(elapsed / toggleInterval);
                const isMouthOpen = biteIndex % 2 === 0;
                
                if (processingDone && !hasErrored && tomX > 420) {
                    tomHeadImg.src = './tom_relief.png?v=5';
                    tomBubble.textContent = "YAM!";
                    tomBubble.className = 'tom-speech-bubble yam';
                    tomBubble.style.opacity = '1';
                    tomBubble.style.transform = 'scale(1.15) rotate(2deg)';
                } else if (tomX > 180 && tomX <= 420) {
                    tomHeadImg.src = isMouthOpen ? './tom_open.png?v=5' : './tom_closed.png?v=5';
                    tomBubble.textContent = "NUM NUM!";
                    tomBubble.className = 'tom-speech-bubble num-num';
                    tomBubble.style.opacity = '1';
                    // Active chomp tilt bounce
                    tomBubble.style.transform = isMouthOpen ? 'scale(1.05) rotate(-3deg)' : 'scale(0.95) rotate(3deg)';
                } else {
                    tomHeadImg.src = isMouthOpen ? './tom_open.png?v=5' : './tom_closed.png?v=5';
                    tomBubble.style.opacity = '0';
                    tomBubble.style.transform = 'scale(0) translateY(10px)';
                }

                // Collision with file 1 (Template) at X=218
                if (tomX > 218 && iconTemplate.style.opacity !== '0') {
                    iconTemplate.style.opacity = '0';
                    iconTemplate.style.transform = 'scale(0)';
                }

                // Collision with file 2 (Data Dump) at X=348
                if (tomX > 348 && iconDump.style.opacity !== '0') {
                    iconDump.style.opacity = '0';
                    iconDump.style.transform = 'scale(0)';
                    animLabel.textContent = "Processing...";
                    
                    // Run actual Excel conversion inside the animation loop!
                    if (!processingDone && !hasErrored) {
                        try {
                            outputBlob = performExcelRemap();
                            processingDone = true;
                        } catch (err) {
                            hasErrored = true;
                            showToast(err.message || "An error occurred during sheet conversion.");
                            resetToDropzone();
                        }
                    }
                }

                // Poop out formatted gold file behind him at X=420
                if (processingDone && !hasErrored && tomX > 420 && iconOutput.style.display === 'none') {
                    iconOutput.style.display = 'block';
                    animLabel.textContent = "Success! File formatted.";
                    animLabel.style.color = "var(--accent-color)";
                }

                // Check bounds
                if (!hasErrored) {
                    if (elapsed < duration) {
                        requestAnimationFrame(animate);
                    } else {
                        // Animation finished, show success box
                        setTimeout(() => {
                            animContainer.style.display = 'none';
                            successBox.style.display = 'block';
                            successFilename.textContent = outputFileName;
                            
                            // Automatically trigger download
                            triggerDownload(outputBlob, outputFileName);
                        }, 500);
                    }
                }
            }

            requestAnimationFrame(animate);
        }

        function resetToDropzone() {
            animContainer.style.display = 'none';
            successBox.style.display = 'none';
            dropzone.style.display = 'block';
            fileInput.value = '';
        }

        resetLink.addEventListener('click', resetToDropzone);

        // Core conversion logic matching Python pandas script
        function performExcelRemap() {
            const sheet = rawExcelData.Sheets['Lots'];
            const json = XLSX.utils.sheet_to_json(sheet);

            if (json.length === 0) {
                throw new Error("No data found in 'Lots' sheet.");
            }

            // Get configuration values from UI inputs
            const sellerNum = document.getElementById('seller-num').value.trim() || '159';
            const location = document.getElementById('location').value.trim() || '166';
            const vatPercentage = document.getElementById('vat-percent').value.trim() || '20';
            const feeVatPercentage = document.getElementById('fee-vat-percent').value.trim() || '2';
            const targetLang = document.getElementById('target-lang').value;

            // Helper to clean up special Excel characters like _x000D_ and non-breaking spaces
            const sanitizeText = (text) => {
                if (!text) return '';
                return String(text).replace(/_x000D_/g, '').replace(/\u00A0/g, ' ').trim();
            };

            // Map rows equivalent to Python logic
            const remappedRows = json.map(row => {
                const outRow = {};

                // Preset language titles/desc to blanks
                let langs = ['en', 'de', 'fr', 'nl', 'it', 'es', 'sv', 'pl'];
                if (auctionSchema && auctionSchema.languages) {
                    langs = auctionSchema.languages;
                }
                langs.forEach(l => {
                    outRow[`title_${l}`] = '';
                    outRow[`description_${l}`] = '';
                });

                // Get mapping from schema or fallback to default
                const mapping = (auctionSchema && auctionSchema.mapping) ? auctionSchema.mapping : {
                    "title": "Title",
                    "description": "Description",
                    "number": "Lotnumber",
                    "starting_bid": "StartingBid",
                    "estimated_price": "EstimatedPrice",
                    "reserve_bid": "ReserveBid",
                    "subcategory": "CategoryDomeId",
                    "brand": "Brand",
                    "attribute-type": "Type",
                    "attribute-year": "Year",
                    "attribute-serial_number": "SerialNumber",
                    "attribute-amount": "Amount",
                    "attribute-buy_amount": "BuyAmount",
                    "needs_manual_allocation": "Allocation",
                    "is_spotlight": "Spotlight"
                };

                // Populate selected language columns
                outRow[`title_${targetLang}`] = sanitizeText(row[mapping['title']]);
                outRow[`description_${targetLang}`] = sanitizeText(row[mapping['description']]);

                outRow['number'] = row[mapping['number']] || '';
                outRow['starting_bid'] = row[mapping['starting_bid']] || '';
                outRow['vat_percentage'] = vatPercentage;
                outRow['fee_vat_percentage'] = feeVatPercentage;
                outRow['estimated_price'] = row[mapping['estimated_price']] || '';
                outRow['reserve_bid'] = row[mapping['reserve_bid']] || '';
                outRow['subcategory'] = row[mapping['subcategory']] || '';
                outRow['location'] = location;
                outRow['seller'] = sellerNum;
                outRow['brand'] = row[mapping['brand']] || '';
                
                // Allocation / Spotlight conversions
                const convertToBinary = (val) => {
                    if (val === true || String(val).trim().toLowerCase() === 'true' || val === 1 || val === '1') {
                        return 1;
                    }
                    return '';
                };

                outRow['needs_manual_allocation'] = (mapping['needs_manual_allocation'] in row) ? convertToBinary(row[mapping['needs_manual_allocation']]) : '';
                outRow['is_spotlight'] = (mapping['is_spotlight'] in row) ? convertToBinary(row[mapping['is_spotlight']]) : '';
                
                outRow['video'] = '';
                outRow['attribute-type'] = row[mapping['attribute-type']] || '';
                outRow['attribute-year'] = row[mapping['attribute-year']] || '';
                outRow['attribute-serial_number'] = row[mapping['attribute-serial_number']] || '';
                outRow['attribute-amount'] = row[mapping['attribute-amount']] || '';
                outRow['attribute-buy_amount'] = row[mapping['attribute-buy_amount']] || '';

                return outRow;
            });

            // Reindex/force column order matching compliant template
            let templateCols = [];
            if (auctionSchema && auctionSchema.template_cols) {
                templateCols = auctionSchema.template_cols;
            } else {
                templateCols = [
                    'title_en', 'title_de', 'title_fr', 'title_nl', 'title_it', 'title_es', 'title_sv', 'title_pl', 
                    'number', 'starting_bid', 'vat_percentage', 'fee_vat_percentage', 'description_en', 'description_de', 
                    'description_fr', 'description_nl', 'description_it', 'description_es', 'description_sv', 'description_pl', 
                    'estimated_price', 'reserve_bid', 'subcategory', 'location', 'seller', 'brand', 
                    'needs_manual_allocation', 'is_spotlight', 'video', 'attribute-type', 'attribute-year', 
                    'attribute-serial_number', 'attribute-amount', 'attribute-buy_amount'
                ];
            }

            const newSheet = XLSX.utils.json_to_sheet(remappedRows, {header: templateCols});
            const newWorkbook = XLSX.utils.book_new();
            XLSX.utils.book_append_sheet(newWorkbook, newSheet, 'Sheet1');

            // Generate binary array
            const outBuffer = XLSX.write(newWorkbook, {bookType: 'xlsx', type: 'array'});
            
            // Save blob
            const blob = new Blob([outBuffer], {type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'});
            
            // Set download click handler
            dlButton.onclick = () => triggerDownload(blob, outputFileName);

            return blob;
        }

        function triggerDownload(blob, filename) {
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            setTimeout(() => URL.revokeObjectURL(url), 2000);
        }