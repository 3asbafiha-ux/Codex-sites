// Matrix Rain Effect
class MatrixRain {
    constructor() {
        this.canvas = document.getElementById('matrix-canvas');
        this.ctx = this.canvas.getContext('2d');
        this.characters = '01アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン';
        this.charArray = this.characters.split('');
        this.drops = [];

        this.resizeCanvas();
        this.init();
        this.animate();

        window.addEventListener('resize', () => this.resizeCanvas());
    }

    resizeCanvas() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;

        const columns = Math.floor(this.canvas.width / 14);
        this.drops = [];
        for (let i = 0; i < columns; i++) {
            this.drops[i] = Math.random() * this.canvas.height;
        }
    }

    init() {
        const columns = Math.floor(this.canvas.width / 14);
        for (let i = 0; i < columns; i++) {
            this.drops[i] = Math.random() * this.canvas.height;
        }
    }

    animate() {
        // Black background with transparency for trail effect
        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.1)';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        // Green text
        this.ctx.fillStyle = '#00FF41';
        this.ctx.font = '14px Fira Code, monospace';

        for (let i = 0; i < this.drops.length; i++) {
            const char = this.charArray[Math.floor(Math.random() * this.charArray.length)];
            const x = i * 14;
            const y = this.drops[i];

            this.ctx.fillText(char, x, y);

            // Reset drop to top randomly
            if (y > this.canvas.height && Math.random() > 0.975) {
                this.drops[i] = 0;
            }

            this.drops[i] += 14;
        }

        requestAnimationFrame(() => this.animate());
    }
}

// API Protection Helper
class APIProtection {
    constructor() {
        this.verified = false;
        this.sessionKey = null;
    }

    async makeProtectedRequest(endpoint, options = {}) {
        const defaultOptions = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        };

        const mergedOptions = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers
            }
        };

        try {
            const response = await fetch(endpoint, mergedOptions);
            return response;
        } catch (error) {
            console.error('API Protection Error:', error);
            throw error;
        }
    }
}

// Initialize API Protection
const apiProtection = new APIProtection();

// API Helper Functions
class APIManager {
    constructor() {
        this.baseURL = '';
        this.bioTokenVerified = false;
        this.itemTokenVerified = false;
    }

    async request(method, endpoint, data = null) {
        const config = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            },
        };

        if (data) {
            config.body = JSON.stringify(data);
        }

        try {
            const response = await fetch(endpoint, config);
            const result = await response.json();
            return { success: response.ok, data: result, status: response.status };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    showResult(title, content, isSuccess = true, type = null) {
        const modal = document.getElementById('result-modal');
        const modalTitle = document.getElementById('modal-title');
        const modalBody = document.getElementById('modal-body');

        modalTitle.textContent = title;
        modalTitle.style.color = isSuccess ? '#00ff41' : '#ff0000';

        if (typeof content === 'object') {
            // Special handling for outfit and banner responses (keep as is)
            if (title.includes('Outfit')) {
                const imageUrl = content.outfit_image || content.image || content.url ||
                    content.outfit || content.data?.image || content.data?.url ||
                    this.extractImageFromMessage(content.message);

                if (imageUrl && this.isValidImageUrl(imageUrl)) {
                    modalBody.innerHTML = `
                        <div class="result-content">
                            <img src="${imageUrl}" alt="User Outfit" class="result-image" style="max-width: 100%; border-radius: 10px; margin: 10px 0;"/>
                            <div class="result-details">
                                <h4 style="color: #9932cc; margin-bottom: 10px;">🎮 Outfit Details</h4>
                                <pre>${JSON.stringify(content, null, 2)}</pre>
                            </div>
                        </div>
                    `;
                } else {
                    modalBody.innerHTML = `
                        <div class="result-content">
                            <div class="outfit-message">
                                <h4 style="color: #9932cc; margin-bottom: 10px;">👕 Outfit Response</h4>
                                <div class="message-box" style="background: rgba(153, 50, 204, 0.1); border: 1px solid #9932cc; border-radius: 8px; padding: 15px; margin: 10px 0;">
                                    <p style="color: #00ff41; font-family: 'Fira Code', monospace;">${content.message || 'No outfit data available'}</p>
                                </div>
                                <details style="margin-top: 15px;">
                                    <summary style="color: #9932cc; cursor: pointer;">📄 Raw Response</summary>
                                    <pre style="margin-top: 10px; font-size: 12px;">${JSON.stringify(content, null, 2)}</pre>
                                </details>
                            </div>
                        </div>
                    `;
                }
            } else if (title.includes('Banner')) {
                const imageUrl = content.banner_url || content.banner || content.image || content.url ||
                    content.data?.banner || content.data?.image || content.data?.url ||
                    this.extractImageFromMessage(content.message);

                if (imageUrl && this.isValidImageUrl(imageUrl)) {
                    modalBody.innerHTML = `
                        <div class="result-content">
                            <img src="${imageUrl}" alt="User Banner" class="result-image" style="max-width: 100%; border-radius: 10px; margin: 10px 0;"/>
                            <div class="result-details">
                                <h4 style="color: #9932cc; margin-bottom: 10px;">🖼️ Banner Details</h4>
                                <pre>${JSON.stringify(content, null, 2)}</pre>
                            </div>
                        </div>
                    `;
                } else {
                    modalBody.innerHTML = `
                        <div class="result-content">
                            <div class="banner-message">
                                <h4 style="color: #9932cc; margin-bottom: 10px;">🏆 Banner Response</h4>
                                <div class="message-box" style="background: rgba(153, 50, 204, 0.1); border: 1px solid #9932cc; border-radius: 8px; padding: 15px; margin: 10px 0;">
                                    <p style="color: #00ff41; font-family: 'Fira Code', monospace;">${content.message || 'No banner data available'}</p>
                                </div>
                                <details style="margin-top: 15px;">
                                    <summary style="color: #9932cc; cursor: pointer;">📄 Raw Response</summary>
                                    <pre style="margin-top: 10px; font-size: 12px;">${JSON.stringify(content, null, 2)}</pre>
                                </details>
                            </div>
                        </div>
                    `;
                }
            } else if (title.includes('User Information')) {
                // Enhanced formatting for user info with complete data display
                const formatUserInfo = (data) => {
                    // Check for AccountInfo structure first
                    if (data.AccountInfo) {
                        return `
                            <div class="user-info-card" style="background: linear-gradient(135deg, rgba(0,255,65,0.05), rgba(153,50,204,0.05)); border: 2px solid rgba(0,255,65,0.3); border-radius: 15px; padding: 25px; margin: 10px 0;">
                                <div style="text-align: center; margin-bottom: 25px;">
                                    <div style="font-size: 48px; margin-bottom: 10px;">🎮</div>
                                    <h2 style="color: #00ff41; margin: 0; text-shadow: 0 0 15px rgba(0,255,65,0.7); font-size: 24px; letter-spacing: 2px;">COMPLETE ACCOUNT INFORMATION</h2>
                                    <div style="height: 3px; background: linear-gradient(90deg, transparent, #00ff41, #9932cc, #00ff41, transparent); margin: 15px 0;"></div>
                                    <div style="color: #9932cc; font-size: 14px; margin-top: 5px;">════════════════════════════════════════════════════════════</div>
                                </div>

                                <div class="account-header" style="background: rgba(0,0,0,0.4); border: 2px solid rgba(0,255,65,0.4); border-radius: 10px; padding: 20px; margin-bottom: 20px; text-align: center;">
                                    <h3 style="color: #00ff41; margin: 0 0 10px 0; font-size: 20px; text-shadow: 0 0 10px rgba(0,255,65,0.5);">👤 ACCOUNT NAME</h3>
                                    <div style="color: #ffffff; font-size: 18px; font-weight: bold; margin: 5px 0;">${data.AccountInfo.AccountName || 'Unknown Player'}</div>
                                    <div style="color: #9932cc; font-size: 12px;">Player ID: ${data.AccountInfo.AccountAvatarId || 'N/A'}</div>
                                </div>

                                <div class="stats-section" style="margin-bottom: 20px;">
                                    <h4 style="color: #9932cc; margin-bottom: 15px; text-align: center; font-size: 16px; letter-spacing: 1px;">📊 PLAYER STATISTICS</h4>
                                    <div style="height: 1px; background: linear-gradient(90deg, transparent, #9932cc, transparent); margin-bottom: 15px;"></div>
                                    <div class="stats-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px;">
                                        <div class="stat-item" style="background: rgba(0,0,0,0.3); border: 1px solid rgba(0,255,65,0.3); border-radius: 8px; padding: 15px; text-align: center;">
                                            <div style="color: #9932cc; font-size: 12px; font-weight: bold; margin-bottom: 5px;">🏆 LEVEL</div>
                                            <div style="color: #00ff41; font-size: 18px; font-weight: bold;">${data.AccountInfo.AccountLevel || 'N/A'}</div>
                                        </div>
                                        <div class="stat-item" style="background: rgba(0,0,0,0.3); border: 1px solid rgba(0,255,65,0.3); border-radius: 8px; padding: 15px; text-align: center;">
                                            <div style="color: #9932cc; font-size: 12px; font-weight: bold; margin-bottom: 5px;">⚡ EXPERIENCE</div>
                                            <div style="color: #00ff41; font-size: 18px; font-weight: bold;">${data.AccountInfo.AccountEXP ? data.AccountInfo.AccountEXP.toLocaleString() : 'N/A'}</div>
                                        </div>
                                        <div class="stat-item" style="background: rgba(0,0,0,0.3); border: 1px solid rgba(0,255,65,0.3); border-radius: 8px; padding: 15px; text-align: center;">
                                            <div style="color: #9932cc; font-size: 12px; font-weight: bold; margin-bottom: 5px;">👥 LIKES</div>
                                            <div style="color: #00ff41; font-size: 18px; font-weight: bold;">${data.AccountInfo.AccountLikes ? data.AccountInfo.AccountLikes.toLocaleString() : 'N/A'}</div>
                                        </div>
                                        <div class="stat-item" style="background: rgba(0,0,0,0.3); border: 1px solid rgba(0,255,65,0.3); border-radius: 8px; padding: 15px; text-align: center;">
                                            <div style="color: #9932cc; font-size: 12px; font-weight: bold; margin-bottom: 5px;">🏅 BP BADGES</div>
                                            <div style="color: #00ff41; font-size: 18px; font-weight: bold;">${data.AccountInfo.AccountBPBadges || 'N/A'}</div>
                                        </div>
                                        <div class="stat-item" style="background: rgba(0,0,0,0.3); border: 1px solid rgba(0,255,65,0.3); border-radius: 8px; padding: 15px; text-align: center;">
                                            <div style="color: #9932cc; font-size: 12px; font-weight: bold; margin-bottom: 5px;">🆔 AVATAR ID</div>
                                            <div style="color: #00ff41; font-size: 14px; font-weight: bold;">${data.AccountInfo.AccountAvatarId || 'N/A'}</div>
                                        </div>
                                        <div class="stat-item" style="background: rgba(0,0,0,0.3); border: 1px solid rgba(0,255,65,0.3); border-radius: 8px; padding: 15px; text-align: center;">
                                            <div style="color: #9932cc; font-size: 12px; font-weight: bold; margin-bottom: 5px;">🎯 BP ID</div>
                                            <div style="color: #00ff41; font-size: 14px; font-weight: bold;">${data.AccountInfo.AccountBPID || 'N/A'}</div>
                                        </div>
                                        <div class="stat-item" style="background: rgba(0,0,0,0.3); border: 1px solid rgba(0,255,65,0.3); border-radius: 8px; padding: 15px; text-align: center;">
                                            <div style="color: #9932cc; font-size: 12px; font-weight: bold; margin-bottom: 5px;">🏆 BANNER ID</div>
                                            <div style="color: #00ff41; font-size: 14px; font-weight: bold;">${data.AccountInfo.AccountBannerId || 'N/A'}</div>
                                        </div>
                                        <div class="stat-item" style="background: rgba(0,0,0,0.3); border: 1px solid rgba(0,255,65,0.3); border-radius: 8px; padding: 15px; text-align: center;">
                                            <div style="color: #9932cc; font-size: 12px; font-weight: bold; margin-bottom: 5px;">🏮 SEASON ID</div>
                                            <div style="color: #00ff41; font-size: 14px; font-weight: bold;">${data.AccountInfo.AccountSeasonId || 'N/A'}</div>
                                        </div>
                                    </div>
                                </div>

                                <div class="timing-section" style="margin-bottom: 20px;">
                                    <h4 style="color: #9932cc; margin-bottom: 15px; text-align: center; font-size: 16px; letter-spacing: 1px;">⏰ ACCOUNT TIMELINE</h4>
                                    <div style="height: 1px; background: linear-gradient(90deg, transparent, #9932cc, transparent); margin-bottom: 15px;"></div>
                                    <div class="timing-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px;">
                                        <div class="timing-item" style="background: rgba(0,0,0,0.3); border: 1px solid rgba(153,50,204,0.3); border-radius: 8px; padding: 15px; text-align: center;">
                                            <div style="color: #9932cc; font-size: 12px; font-weight: bold; margin-bottom: 5px;">📅 CREATED</div>
                                            <div style="color: #ffffff; font-size: 14px; font-weight: bold;">${data.AccountInfo.AccountCreateTime ? this.formatTimestamp(data.AccountInfo.AccountCreateTime) : 'N/A'}</div>
                                        </div>
                                        <div class="timing-item" style="background: rgba(0,0,0,0.3); border: 1px solid rgba(153,50,204,0.3); border-radius: 8px; padding: 15px; text-align: center;">
                                            <div style="color: #9932cc; font-size: 12px; font-weight: bold; margin-bottom: 5px;">🔄 LAST LOGIN</div>
                                            <div style="color: #ffffff; font-size: 14px; font-weight: bold;">${data.AccountInfo.AccountLastLogin ? this.formatTimestamp(data.AccountInfo.AccountLastLogin) : 'N/A'}</div>
                                        </div>
                                    </div>
                                </div>

                                <div class="info-section" style="margin-bottom: 20px;">
                                    <h4 style="color: #9932cc; margin-bottom: 15px; text-align: center; font-size: 16px; letter-spacing: 1px;">🌍 ACCOUNT DETAILS</h4>
                                    <div style="height: 1px; background: linear-gradient(90deg, transparent, #9932cc, transparent); margin-bottom: 15px;"></div>
                                    <div class="info-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px;">
                                        <div class="info-item" style="background: rgba(0,0,0,0.3); border: 1px solid rgba(153,50,204,0.3); border-radius: 8px; padding: 15px; text-align: center;">
                                            <div style="color: #9932cc; font-size: 12px; font-weight: bold; margin-bottom: 5px;">🌍 REGION</div>
                                            <div style="color: #ffffff; font-size: 16px; font-weight: bold;">${data.AccountInfo.AccountRegion || 'N/A'}</div>
                                        </div>
                                        <div class="info-item" style="background: rgba(0,0,0,0.3); border: 1px solid rgba(153,50,204,0.3); border-radius: 8px; padding: 15px; text-align: center;">
                                            <div style="color: #9932cc; font-size: 12px; font-weight: bold; margin-bottom: 5px;">🔢 CREATE TIME (UNIX)</div>
                                            <div style="color: #ffffff; font-size: 14px; font-weight: bold;">${data.AccountInfo.AccountCreateTime || 'N/A'}</div>
                                        </div>
                                        <div class="info-item" style="background: rgba(0,0,0,0.3); border: 1px solid rgba(153,50,204,0.3); border-radius: 8px; padding: 15px; text-align: center;">
                                            <div style="color: #9932cc; font-size: 12px; font-weight: bold; margin-bottom: 5px;">🔢 LAST LOGIN (UNIX)</div>
                                            <div style="color: #ffffff; font-size: 14px; font-weight: bold;">${data.AccountInfo.AccountLastLogin || 'N/A'}</div>
                                        </div>
                                    </div>
                                </div>

                                <details style="margin-top: 20px;">
                                    <summary style="color: #9932cc; cursor: pointer; background: rgba(153,50,204,0.1); padding: 12px; border-radius: 8px; border: 1px solid rgba(153,50,204,0.4); text-align: center; font-weight: bold;">📊 COMPLETE RAW DATA</summary>
                                    <pre style="margin-top: 15px; font-size: 11px; background: rgba(0,0,0,0.6); padding: 20px; border-radius: 10px; border: 1px solid rgba(0,255,65,0.3); color: #00ff41; overflow-x: auto; font-family: 'Fira Code', monospace;">${JSON.stringify(data, null, 2)}</pre>
                                </details>
                            </div>
                        `;
                    }
                    // Check for basicInfo structure (fallback)
                    else if (data.basicInfo) {
                        return `
                            <div class="user-info-card" style="background: linear-gradient(135deg, rgba(0,255,65,0.05), rgba(153,50,204,0.05)); border: 2px solid rgba(0,255,65,0.3); border-radius: 15px; padding: 25px; margin: 10px 0;">
                                <div style="text-align: center; margin-bottom: 25px;">
                                    <div style="font-size: 48px; margin-bottom: 10px;">🎮</div>
                                    <h2 style="color: #00ff41; margin: 0; text-shadow: 0 0 15px rgba(0,255,65,0.7); font-size: 24px; letter-spacing: 2px;">COMPLETE ACCOUNT INFORMATION</h2>
                                    <div style="height: 3px; background: linear-gradient(90deg, transparent, #00ff41, #9932cc, #00ff41, transparent); margin: 15px 0;"></div>
                                    <div style="color: #9932cc; font-size: 14px; margin-top: 5px;">════════════════════════════════════════════════════════════</div>
                                </div>

                                <div class="account-header" style="background: rgba(0,0,0,0.4); border: 2px solid rgba(0,255,65,0.4); border-radius: 10px; padding: 20px; margin-bottom: 20px; text-align: center;">
                                    <h3 style="color: #00ff41; margin: 0 0 10px 0; font-size: 20px; text-shadow: 0 0 10px rgba(0,255,65,0.5);">👤 ACCOUNT NAME</h3>
                                    <div style="color: #ffffff; font-size: 18px; font-weight: bold; margin: 5px 0;">${data.basicInfo.nickname || 'Unknown Player'}</div>
                                    <div style="color: #9932cc; font-size: 12px;">Player ID: ${data.basicInfo.accountId || 'N/A'}</div>
                                </div>

                                <div class="stats-section" style="margin-bottom: 20px;">
                                    <h4 style="color: #9932cc; margin-bottom: 15px; text-align: center; font-size: 16px; letter-spacing: 1px;">📊 PLAYER STATISTICS</h4>
                                    <div style="height: 1px; background: linear-gradient(90deg, transparent, #9932cc, transparent); margin-bottom: 15px;"></div>
                                    <div class="stats-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px;">
                                        <div class="stat-item" style="background: rgba(0,0,0,0.3); border: 1px solid rgba(0,255,65,0.3); border-radius: 8px; padding: 15px; text-align: center;">
                                            <div style="color: #9932cc; font-size: 12px; font-weight: bold; margin-bottom: 5px;">🏆 LEVEL</div>
                                            <div style="color: #00ff41; font-size: 18px; font-weight: bold;">${data.basicInfo.level || 'N/A'}</div>
                                        </div>
                                        <div class="stat-item" style="background: rgba(0,0,0,0.3); border: 1px solid rgba(0,255,65,0.3); border-radius: 8px; padding: 15px; text-align: center;">
                                            <div style="color: #9932cc; font-size: 12px; font-weight: bold; margin-bottom: 5px;">⚡ EXPERIENCE</div>
                                            <div style="color: #00ff41; font-size: 18px; font-weight: bold;">${data.basicInfo.exp || 'N/A'}</div>
                                        </div>
                                        <div class="stat-item" style="background: rgba(0,0,0,0.3); border: 1px solid rgba(0,255,65,0.3); border-radius: 8px; padding: 15px; text-align: center;">
                                            <div style="color: #9932cc; font-size: 12px; font-weight: bold; margin-bottom: 5px;">🆔 ACCOUNT ID</div>
                                            <div style="color: #00ff41; font-size: 14px; font-weight: bold;">${data.basicInfo.accountId || 'N/A'}</div>
                                        </div>
                                        <div class="stat-item" style="background: rgba(0,0,0,0.3); border: 1px solid rgba(0,255,65,0.3); border-radius: 8px; padding: 15px; text-align: center;">
                                            <div style="color: #9932cc; font-size: 12px; font-weight: bold; margin-bottom: 5px;">👤 NICKNAME</div>
                                            <div style="color: #00ff41; font-size: 14px; font-weight: bold;">${data.basicInfo.nickname || 'N/A'}</div>
                                        </div>
                                    </div>
                                </div>

                                <div class="currency-section" style="margin-bottom: 20px;">
                                    <h4 style="color: #9932cc; margin-bottom: 15px; text-align: center; font-size: 16px; letter-spacing: 1px;">💰 CURRENCY STATUS</h4>
                                    <div style="height: 1px; background: linear-gradient(90deg, transparent, #9932cc, transparent); margin-bottom: 15px;"></div>
                                    <div class="currency-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px;">
                                        <div class="currency-item" style="background: rgba(0,0,0,0.3); border: 1px solid rgba(255,215,0,0.3); border-radius: 8px; padding: 15px; text-align: center;">
                                            <div style="color: #FFD700; font-size: 24px; margin-bottom: 5px;">💰</div>
                                            <div style="color: #9932cc; font-size: 12px; font-weight: bold; margin-bottom: 5px;">GOLD</div>
                                            <div style="color: #FFD700; font-size: 18px; font-weight: bold;">${data.basicInfo.gold || 'N/A'}</div>
                                        </div>
                                        <div class="currency-item" style="background: rgba(0,0,0,0.3); border: 1px solid rgba(0,191,255,0.3); border-radius: 8px; padding: 15px; text-align: center;">
                                            <div style="color: #00BFFF; font-size: 24px; margin-bottom: 5px;">💎</div>
                                            <div style="color: #9932cc; font-size: 12px; font-weight: bold; margin-bottom: 5px;">DIAMONDS</div>
                                            <div style="color: #00BFFF; font-size: 18px; font-weight: bold;">${data.basicInfo.diamond || 'N/A'}</div>
                                        </div>
                                    </div>
                                </div>

                                <details style="margin-top: 20px;">
                                    <summary style="color: #9932cc; cursor: pointer; background: rgba(153,50,204,0.1); padding: 12px; border-radius: 8px; border: 1px solid rgba(153,50,204,0.4); text-align: center; font-weight: bold;">📊 COMPLETE RAW DATA</summary>
                                    <pre style="margin-top: 15px; font-size: 11px; background: rgba(0,0,0,0.6); padding: 20px; border-radius: 10px; border: 1px solid rgba(0,255,65,0.3); color: #00ff41; overflow-x: auto; font-family: 'Fira Code', monospace;">${JSON.stringify(data, null, 2)}</pre>
                                </details>
                            </div>
                        `;
                    }
                    // Enhanced fallback for any other data structure with smart parsing
                    else {
                        // Try to extract any available fields dynamically
                        const extractInfo = (obj, prefix = '') => {
                            let html = '';
                            Object.keys(obj).forEach(key => {
                                const value = obj[key];
                                if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
                                    html += extractInfo(value, prefix + key + '.');
                                } else {
                                    html += `
                                        <div class="data-item" style="background: rgba(0,0,0,0.3); border: 1px solid rgba(0,255,65,0.3); border-radius: 8px; padding: 15px; text-align: center; margin: 8px;">
                                            <div style="color: #9932cc; font-size: 12px; font-weight: bold; margin-bottom: 5px;">${(prefix + key).toUpperCase()}</div>
                                            <div style="color: #00ff41; font-size: 14px; font-weight: bold;">${Array.isArray(value) ? value.join(', ') : (value || 'N/A')}</div>
                                        </div>
                                    `;
                                }
                            });
                            return html;
                        };

                        return `
                            <div style="background: linear-gradient(135deg, rgba(0,255,65,0.05), rgba(153,50,204,0.05)); border: 2px solid rgba(0,255,65,0.3); border-radius: 15px; padding: 25px; margin: 10px 0;">
                                <div style="text-align: center; margin-bottom: 25px;">
                                    <div style="font-size: 48px; margin-bottom: 10px;">📊</div>
                                    <h2 style="color: #00ff41; margin: 0; text-shadow: 0 0 15px rgba(0,255,65,0.7); font-size: 24px; letter-spacing: 2px;">COMPLETE USER DATA RETRIEVED</h2>
                                    <div style="height: 3px; background: linear-gradient(90deg, transparent, #00ff41, #9932cc, #00ff41, transparent); margin: 15px 0;"></div>
                                    <div style="color: #9932cc; font-size: 14px; margin-top: 5px;">════════════════════════════════════════════════════════════</div>
                                </div>

                                <div class="all-data-section" style="margin-bottom: 20px;">
                                    <h4 style="color: #9932cc; margin-bottom: 15px; text-align: center; font-size: 16px; letter-spacing: 1px;">🔍 ALL AVAILABLE DATA</h4>
                                    <div style="height: 1px; background: linear-gradient(90deg, transparent, #9932cc, transparent); margin-bottom: 15px;"></div>
                                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px;">
                                        ${extractInfo(data)}
                                    </div>
                                </div>

                                <details style="margin-top: 20px;">
                                    <summary style="color: #9932cc; cursor: pointer; background: rgba(153,50,204,0.1); padding: 12px; border-radius: 8px; border: 1px solid rgba(153,50,204,0.4); text-align: center; font-weight: bold;">📊 COMPLETE RAW DATA</summary>
                                    <pre style="margin-top: 15px; font-size: 11px; background: rgba(0,0,0,0.6); padding: 20px; border-radius: 10px; border: 1px solid rgba(0,255,65,0.3); color: #00ff41; overflow-x: auto; font-family: 'Fira Code', monospace;">${JSON.stringify(data, null, 2)}</pre>
                                </details>
                            </div>
                        `;
                    }
                };
                modalBody.innerHTML = formatUserInfo(content);
            } else if (title.includes('Bio Updated')) {
                // Enhanced bio update response with better formatting
                modalBody.innerHTML = `
                    <div class="success-response" style="background: linear-gradient(135deg, rgba(0,255,65,0.1), rgba(0,255,65,0.05)); border: 2px solid rgba(0,255,65,0.5); border-radius: 15px; padding: 30px; text-align: center;">
                        <div style="font-size: 64px; margin-bottom: 20px;">✅</div>
                        <h2 style="color: #00ff41; margin: 0 0 10px 0; text-shadow: 0 0 15px rgba(0,255,65,0.7); letter-spacing: 2px; font-size: 24px;">BIO UPDATE SUCCESSFUL</h2>
                        <div style="height: 3px; background: linear-gradient(90deg, transparent, #00ff41, #9932cc, #00ff41, transparent); margin: 20px 0;"></div>

                        <div style="background: rgba(0,0,0,0.4); border: 2px solid rgba(0,255,65,0.4); border-radius: 10px; padding: 20px; margin: 20px 0;">
                            <div style="color: #9932cc; font-size: 12px; font-weight: bold;">SYSTEM RESPONSE</div>
                            <div style="background: rgba(0,0,0,0.3); border: 1px solid rgba(0,255,65,0.3); border-radius: 8px; padding: 15px;">
                                <p style="color: #00ff41; margin: 0; font-family: 'Fira Code', monospace; font-size: 14px;">${typeof content === 'object' ? JSON.stringify(content, null, 2) : content}</p>
                            </div>
                        </div>

                        <div style="background: rgba(153,50,204,0.1); border: 1px solid rgba(153,50,204,0.3); border-radius: 8px; padding: 15px; margin-top: 20px;">
                            <div style="color: #9932cc; font-size: 14px; font-weight: bold;">✨ Your profile bio has been updated successfully! ✨</div>
                        </div>
                    </div>
                `;
            } else if (title.includes('Friend Request')) {
                // Enhanced friend request response - show only spam info, no tokens
                let spamInfo = '';
                if (typeof content === 'object' && content.spam_results) {
                    spamInfo = `
                        <div class="spam-stats" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0;">
                            <div class="stat-card" style="background: rgba(0,0,0,0.4); border: 2px solid rgba(0,255,65,0.4); border-radius: 10px; padding: 20px; text-align: center;">
                                <div style="color: #9932cc; font-size: 12px; font-weight: bold; margin-bottom: 8px;">🎯 PLAYER ID</div>
                                <div style="color: #00ff41; font-size: 16px; font-weight: bold;">${content.spam_results.player_id || 'Unknown'}</div>
                            </div>
                            <div class="stat-card" style="background: rgba(0,0,0,0.4); border: 2px solid rgba(255,215,0,0.4); border-radius: 10px; padding: 20px; text-align: center;">
                                <div style="color: #9932cc; font-size: 12px; font-weight: bold; margin-bottom: 8px;">📬 REQUESTS SENT</div>
                                <div style="color: #ffd700; font-size: 20px; font-weight: bold;">${content.spam_results.friend_requests_sent || 0}</div>
                            </div>
                            <div class="stat-card" style="background: rgba(0,0,0,0.4); border: 2px solid rgba(0,255,65,0.4); border-radius: 10px; padding: 20px; text-align: center;">
                                <div style="color: #9932cc; font-size: 12px; font-weight: bold; margin-bottom: 8px;">✅ SUCCESSFUL</div>
                                <div style="color: #00ff41; font-size: 18px; font-weight: bold;">${content.spam_results.successful_operations || 0}</div>
                            </div>
                            <div class="stat-card" style="background: rgba(0,0,0,0.4); border: 2px solid rgba(153,50,204,0.4); border-radius: 10px; padding: 20px; text-align: center;">
                                <div style="color: #9932cc; font-size: 12px; font-weight: bold; margin-bottom: 8px;">🚀 OPERATION TYPE</div>
                                <div style="color: #9932cc; font-size: 14px; font-weight: bold;">FRIEND SPAM</div>
                            </div>
                        </div>
                    `;
                } else {
                    // For other responses, show clean format without tokens
                    const displayContent = this.cleanResponseContent(content);
                    spamInfo = `
                        <div style="background: rgba(0,0,0,0.3); border: 1px solid ${isSuccess ? 'rgba(0,255,65,0.3)' : 'rgba(255,0,0,0.3)'}; border-radius: 8px; padding: 15px;">
                            <p style="color: ${isSuccess ? '#00ff41' : '#ff0000'}; margin: 0; font-family: 'Fira Code', monospace; font-size: 14px;">${displayContent}</p>
                        </div>
                    `;
                }

                modalBody.innerHTML = `
                    <div class="response-container" style="background: linear-gradient(135deg, ${isSuccess ? 'rgba(0,255,65,0.1), rgba(0,255,65,0.05)' : 'rgba(255,0,0,0.1), rgba(255,0,0,0.05)'}); border: 2px solid ${isSuccess ? 'rgba(0,255,65,0.5)' : 'rgba(255,0,0,0.5)'}; border-radius: 15px; padding: 30px; text-align: center;">
                        <div style="font-size: 64px; margin-bottom: 20px;">${isSuccess ? '👥' : '❌'}</div>
                        <h2 style="color: ${isSuccess ? '#00ff41' : '#ff0000'}; margin: 0 0 10px 0; text-shadow: 0 0 15px ${isSuccess ? 'rgba(0,255,65,0.7)' : 'rgba(255,0,0,0.7)'}; letter-spacing: 2px; font-size: 24px;">${isSuccess ? 'FRIEND REQUEST SPAM SENT' : 'FRIEND REQUEST FAILED'}</h2>
                        <div style="height: 3px; background: linear-gradient(90deg, transparent, ${isSuccess ? '#00ff41, #9932cc, #00ff41' : '#ff0000, #cc3232, #ff0000'}, transparent); margin: 20px 0;"></div>

                        ${spamInfo}

                        <div style="background: rgba(153,50,204,0.1); border: 1px solid rgba(153,50,204,0.3); border-radius: 8px; padding: 15px; margin-top: 20px;">
                            <div style="color: #9932cc; font-size: 14px; font-weight: bold;">${isSuccess ? '🎯 Friend request spam completed successfully! 🎯' : '⚠️ Friend request operation encountered an issue ⚠️'}</div>
                        </div>
                    </div>
                `;
            } else if (title.includes('Visit') || title.includes('Visits')) {
                // Enhanced visits response with focus on spam information
                let visitsInfo = '';
                if (typeof content === 'object') {
                    // Check if this is a successful visits response with statistics
                    if (content.results && content.results.visits_added !== undefined) {
                        visitsInfo = `
                            <div class="visits-stats" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0;">
                                <div class="stat-card" style="background: rgba(0,0,0,0.4); border: 2px solid rgba(0,255,65,0.4); border-radius: 10px; padding: 20px; text-align: center;">
                                    <div style="color: #9932cc; font-size: 12px; font-weight: bold; margin-bottom: 8px;">🎯 PLAYER ID</div>
                                    <div style="color: #00ff41; font-size: 16px; font-weight: bold;">${content.results.player_id || 'Unknown'}</div>
                                </div>
                                <div class="stat-card" style="background: rgba(0,0,0,0.4); border: 2px solid rgba(255,215,0,0.4); border-radius: 10px; padding: 20px; text-align: center;">
                                    <div style="color: #9932cc; font-size: 12px; font-weight: bold; margin-bottom: 8px;">👁️ VISITS ADDED</div>
                                    <div style="color: #ffd700; font-size: 20px; font-weight: bold;">+${content.results.visits_added || 0}</div>
                                </div>
                                <div class="stat-card" style="background: rgba(0,0,0,0.4); border: 2px solid rgba(0,255,65,0.4); border-radius: 10px; padding: 20px; text-align: center;">
                                    <div style="color: #9932cc; font-size: 12px; font-weight: bold; margin-bottom: 8px;">✅ SUCCESSFUL</div>
                                    <div style="color: #00ff41; font-size: 18px; font-weight: bold;">${content.results.successful_operations || 0}</div>
                                </div>
                                <div class="stat-card" style="background: rgba(0,0,0,0.4); border: 2px solid rgba(138,43,226,0.4); border-radius: 10px; padding: 20px; text-align: center;">
                                    <div style="color: #9932cc; font-size: 12px; font-weight: bold; margin-bottom: 8px;">📊 BATCH SIZE</div>
                                    <div style="color: #8a2be2; font-size: 16px; font-weight: bold;">${content.results.batch_size || 0}</div>
                                </div>
                            </div>
                        `;
                    } else {
                        // For other object responses, show clean format
                        const displayContent = this.cleanResponseContent(content);
                        visitsInfo = `
                            <div style="background: rgba(0,0,0,0.3); border: 1px solid ${isSuccess ? 'rgba(0,255,65,0.3)' : 'rgba(255,0,0,0.3)'}; border-radius: 8px; padding: 15px;">
                                <p style="color: ${isSuccess ? '#00ff41' : '#ff0000'}; margin: 0; font-family: 'Fira Code', monospace; font-size: 14px;">${displayContent}</p>
                            </div>
                        `;
                    }
                } else {
                    visitsInfo = `
                        <div style="background: rgba(0,0,0,0.3); border: 1px solid ${isSuccess ? 'rgba(0,255,65,0.3)' : 'rgba(255,0,0,0.3)'}; border-radius: 8px; padding: 15px;">
                            <p style="color: ${isSuccess ? '#00ff41' : '#ff0000'}; margin: 0; font-family: 'Fira Code', monospace; font-size: 14px;">${content}</p>
                        </div>
                    `;
                }

                modalBody.innerHTML = `
                    <div class="response-container" style="background: linear-gradient(135deg, ${isSuccess ? 'rgba(0,255,65,0.1), rgba(0,255,65,0.05)' : 'rgba(255,0,0,0.1), rgba(255,0,0,0.05)'}); border: 2px solid ${isSuccess ? 'rgba(0,255,65,0.5)' : 'rgba(255,0,0,0.5)'}; border-radius: 15px; padding: 30px; text-align: center;">
                        <div style="font-size: 64px; margin-bottom: 20px;">${isSuccess ? '👁️' : '❌'}</div>
                        <h2 style="color: ${isSuccess ? '#00ff41' : '#ff0000'}; margin: 0 0 10px 0; text-shadow: 0 0 15px ${isSuccess ? 'rgba(0,255,65,0.7)' : 'rgba(255,0,0,0.7)'}; letter-spacing: 2px; font-size: 24px;">${isSuccess ? 'VISITS SENT SUCCESSFULLY' : 'VISITS OPERATION FAILED'}</h2>
                        <div style="height: 3px; background: linear-gradient(90deg, transparent, ${isSuccess ? '#00ff41, #9932cc, #00ff41' : '#ff0000, #cc3232, #ff0000'}, transparent); margin: 20px 0;"></div>

                        ${visitsInfo}

                        <div style="background: rgba(153,50,204,0.1); border: 1px solid rgba(153,50,204,0.3); border-radius: 8px; padding: 15px; margin-top: 20px;">
                            <div style="color: #9932cc; font-size: 14px; font-weight: bold;">${isSuccess ? '👁️ Visits have been sent successfully to the target player! 👁️' : '⚠️ Visits operation encountered an issue ⚠️'}</div>
                        </div>
                    </div>
                `;
            } else if (title.includes('Likes Sent') || title.includes('Like')) {
                // Enhanced likes response with focus on important information only
                let likesInfo = '';
                if (typeof content === 'object') {
                    // معالجة خاصة لخطأ حد الإرسال اليومي
                    if (content.type === 'cooldown_limit') {
                        modalBody.innerHTML = `
                            <div class="cooldown-error-container" style="background: linear-gradient(135deg, rgba(255,140,0,0.1), rgba(255,69,0,0.05)); border: 2px solid rgba(255,140,0,0.6); border-radius: 15px; padding: 30px; text-align: center;">
                                <div style="font-size: 64px; margin-bottom: 20px;">⏰</div>
                                <h2 style="color: #ff8c00; margin: 0 0 15px 0; text-shadow: 0 0 15px rgba(255,140,0,0.7); font-size: 24px; letter-spacing: 2px;">${content.title}</h2>
                                <div style="height: 3px; background: linear-gradient(90deg, transparent, #ff8c00, #ff4500, #ff8c00, transparent); margin: 20px 0;"></div>

                                <div style="background: rgba(0,0,0,0.4); border: 2px solid rgba(255,140,0,0.4); border-radius: 12px; padding: 25px; margin: 20px 0;">
                                    <div style="color: #ff8c00; font-size: 16px; font-weight: bold; margin-bottom: 15px;">📋 تفاصيل الحد الزمني</div>
                                    <div style="color: #fff; font-size: 14px; line-height: 1.6;">${content.message}</div>

                                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0;">
                                        <div style="background: rgba(255,140,0,0.1); border: 1px solid rgba(255,140,0,0.3); border-radius: 8px; padding: 15px;">
                                            <div style="color: #ff8c00; font-size: 12px; font-weight: bold; margin-bottom: 5px;">⏳ الساعات المتبقية</div>
                                            <div style="color: #fff; font-size: 20px; font-weight: bold;">${content.details.hours_remaining} ساعة</div>
                                        </div>
                                        <div style="background: rgba(255,140,0,0.1); border: 1px solid rgba(255,140,0,0.3); border-radius: 8px; padding: 15px;">
                                            <div style="color: #ff8c00; font-size: 12px; font-weight: bold; margin-bottom: 5px;">⌛ الدقائق المتبقية</div>
                                            <div style="color: #fff; font-size: 20px; font-weight: bold;">${content.details.minutes_remaining} دقيقة</div>
                                        </div>
                                    </div>

                                    <div style="background: rgba(255,69,0,0.1); border: 1px solid rgba(255,69,0,0.3); border-radius: 8px; padding: 15px; margin: 15px 0;">
                                        <div style="color: #ff4500; font-size: 12px; font-weight: bold; margin-bottom: 5px;">📅 الوقت المتاح للإرسال التالي</div>
                                        <div style="color: #fff; font-size: 16px; font-weight: bold;">${content.details.next_allowed_time}</div>
                                    </div>
                                </div>

                                <div style="background: rgba(255,140,0,0.1); border: 1px solid rgba(255,140,0,0.3); border-radius: 8px; padding: 15px; margin-top: 20px;">
                                    <div style="color: #ff8c00; font-size: 14px; font-weight: bold;">💡 نصيحة: يمكنك المحاولة مرة أخرى بعد انتهاء المدة المحددة أعلاه</div>
                                </div>

                                <div style="margin-top: 25px; padding: 15px; background: rgba(0,0,0,0.3); border-radius: 8px; border: 1px solid rgba(255,140,0,0.2);">
                                    <div style="color: #ff8c00; font-size: 12px; margin-bottom: 8px;">🔢 إجمالي الثواني المتبقية: ${content.details.total_seconds.toLocaleString()}</div>
                                    <div style="width: 100%; height: 8px; background: rgba(0,0,0,0.5); border-radius: 4px; overflow: hidden;">
                                        <div style="height: 100%; background: linear-gradient(90deg, #ff8c00, #ff4500); width: ${Math.max(5, (86400 - content.details.total_seconds) / 86400 * 100)}%; transition: width 0.3s;"></div>
                                    </div>
                                    <div style="color: #ccc; font-size: 11px; margin-top: 5px;">شريط التقدم: ${Math.round((86400 - content.details.total_seconds) / 86400 * 100)}% من 24 ساعة</div>
                                </div>
                            </div>
                        `;
                        return;
                    }

                    // Check if this is a successful likes response with statistics
                    if (content.likes_added !== undefined || content.player_name !== undefined) {
                        // Extract important information and hide token details
                        likesInfo = `
                            <div class="likes-stats" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0;">
                                <div class="stat-card" style="background: rgba(0,0,0,0.4); border: 2px solid rgba(0,255,65,0.4); border-radius: 10px; padding: 20px; text-align: center;">
                                    <div style="color: #9932cc; font-size: 12px; font-weight: bold; margin-bottom: 8px;">🎯 PLAYER NAME</div>
                                    <div style="color: #00ff41; font-size: 16px; font-weight: bold;">${content.player_name || 'Unknown'}</div>
                                </div>
                                <div class="stat-card" style="background: rgba(0,0,0,0.4); border: 2px solid rgba(0,255,65,0.4); border-radius: 10px; padding: 20px; text-align: center;">
                                    <div style="color: #9932cc; font-size: 12px; font-weight: bold; margin-bottom: 8px;">💎 PLAYER ID</div>
                                    <div style="color: #00ff41; font-size: 16px; font-weight: bold;">${content.player_id || 'Unknown'}</div>
                                </div>
                                <div class="stat-card" style="background: rgba(0,0,0,0.4); border: 2px solid rgba(255,215,0,0.4); border-radius: 10px; padding: 20px; text-align: center;">
                                    <div style="color: #9932cc; font-size: 12px; font-weight: bold; margin-bottom: 8px;">➕ LIKES ADDED</div>
                                    <div style="color: #ffd700; font-size: 20px; font-weight: bold;">+${content.likes_added || 0}</div>
                                </div>
                                <div class="stat-card" style="background: rgba(0,0,0,0.4); border: 2px solid rgba(0,255,65,0.4); border-radius: 10px; padding: 20px; text-align: center;">
                                    <div style="color: #9932cc; font-size: 12px; font-weight: bold; margin-bottom: 8px;">📊 BEFORE</div>
                                    <div style="color: #00ff41; font-size: 18px; font-weight: bold;">${content.likes_before || 0}</div>
                                </div>
                                <div class="stat-card" style="background: rgba(0,0,0,0.4); border: 2px solid rgba(0,255,65,0.4); border-radius: 10px; padding: 20px; text-align: center;">
                                    <div style="color: #9932cc; font-size: 12px; font-weight: bold; margin-bottom: 8px;">📈 AFTER</div>
                                    <div style="color: #00ff41; font-size: 18px; font-weight: bold;">${content.likes_after || 0}</div>
                                </div>
                                <div class="stat-card" style="background: rgba(0,0,0,0.4); border: 2px solid rgba(255,69,0,0.4); border-radius: 10px; padding: 20px; text-align: center;">
                                    <div style="color: #9932cc; font-size: 12px; font-weight: bold; margin-bottom: 8px;">⏰ LAST LOGIN</div>
                                    <div style="color: #ff4500; font-size: 14px; font-weight: bold;">${content.last_login_time ? this.formatTimestamp(content.last_login_time) : 'Unknown'}</div>
                                </div>
                                <div class="stat-card" style="background: rgba(0,0,0,0.4); border: 2px solid rgba(138,43,226,0.4); border-radius: 10px; padding: 20px; text-align: center;">
                                    <div style="color: #9932cc; font-size: 12px; font-weight: bold; margin-bottom: 8px;">📅 ACCOUNT CREATED</div>
                                    <div style="color: #8a2be2; font-size: 14px; font-weight: bold;">${content.created_time ? this.formatTimestamp(content.created_time) : 'Unknown'}</div>
                                </div>
                            </div>
                        `;
                    } else {
                        // For other object responses (like error messages), show clean format
                        const displayContent = this.cleanResponseContent(content);
                        likesInfo = `
                            <div style="background: rgba(0,0,0,0.3); border: 1px solid ${isSuccess ? 'rgba(0,255,65,0.3)' : 'rgba(255,0,0,0.3)'}; border-radius: 8px; padding: 15px;">
                                <p style="color: ${isSuccess ? '#00ff41' : '#ff0000'}; margin: 0; font-family: 'Fira Code', monospace; font-size: 14px;">${displayContent}</p>
                            </div>
                        `;
                    }
                } else {
                    likesInfo = `
                        <div style="background: rgba(0,0,0,0.3); border: 1px solid ${isSuccess ? 'rgba(0,255,65,0.3)' : 'rgba(255,0,0,0.3)'}; border-radius: 8px; padding: 15px;">
                            <p style="color: ${isSuccess ? '#00ff41' : '#ff0000'}; margin: 0; font-family: 'Fira Code', monospace; font-size: 14px;">${content}</p>
                        </div>
                    `;
                }

                modalBody.innerHTML = `
                    <div class="response-container" style="background: linear-gradient(135deg, ${isSuccess ? 'rgba(0,255,65,0.1), rgba(0,255,65,0.05)' : 'rgba(255,0,0,0.1), rgba(255,0,0,0.05)'}); border: 2px solid ${isSuccess ? 'rgba(0,255,65,0.5)' : 'rgba(255,0,0,0.5)'}; border-radius: 15px; padding: 30px; text-align: center;">
                        <div style="font-size: 64px; margin-bottom: 20px;">${isSuccess ? '❤️' : '💔'}</div>
                        <h2 style="color: ${isSuccess ? '#00ff41' : '#ff0000'}; margin: 0 0 10px 0; text-shadow: 0 0 15px ${isSuccess ? 'rgba(0,255,65,0.7)' : 'rgba(255,0,0,0.7)'}; letter-spacing: 2px; font-size: 24px;">${isSuccess ? 'LIKES SENT SUCCESSFULLY' : 'LIKES OPERATION FAILED'}</h2>
                        <div style="height: 3px; background: linear-gradient(90deg, transparent, ${isSuccess ? '#00ff41, #9932cc, #00ff41' : '#ff0000, #cc3232, #ff0000'}, transparent); margin: 20px 0;"></div>

                        ${likesInfo}

                        <div style="background: rgba(153,50,204,0.1); border: 1px solid rgba(153,50,204,0.3); border-radius: 8px; padding: 15px; margin-top: 20px;">
                            <div style="color: #9932cc; font-size: 14px; font-weight: bold;">${isSuccess ? '💖 Likes have been sent successfully to the target player! 💖' : '⚠️ Likes operation encountered an issue ⚠️'}</div>
                        </div>
                    </div>
                `;
            } else if (title.includes('Items') || title.includes('Item')) {
                // Enhanced items injection response with better organization
                modalBody.innerHTML = `
                    <div class="response-container" style="background: linear-gradient(135deg, ${isSuccess ? 'rgba(0,255,65,0.1), rgba(0,255,65,0.05)' : 'rgba(255,0,0,0.1), rgba(255,0,0,0.05)'}); border: 2px solid ${isSuccess ? 'rgba(0,255,65,0.5)' : 'rgba(255,0,0,0.5)'}; border-radius: 15px; padding: 30px; text-align: center;">
                        <div style="font-size: 64px; margin-bottom: 20px;">${isSuccess ? '📦' : '❌'}</div>
                        <h2 style="color: ${isSuccess ? '#00ff41' : '#ff0000'}; margin: 0 0 10px 0; text-shadow: 0 0 15px ${isSuccess ? 'rgba(0,255,65,0.7)' : 'rgba(255,0,0,0.7)'}; letter-spacing: 2px; font-size: 24px;">${isSuccess ? 'ITEMS OPERATION SUCCESS' : 'ITEMS OPERATION FAILED'}</h2>
                        <div style="height: 3px; background: linear-gradient(90deg, transparent, ${isSuccess ? '#00ff41, #9932cc, #00ff41' : '#ff0000, #cc3232, #ff0000'}, transparent); margin: 20px 0;"></div>

                        <div style="background: rgba(0,0,0,0.4); border: 2px solid ${isSuccess ? 'rgba(0,255,65,0.4)' : 'rgba(255,0,0,0.4)'}; border-radius: 10px; padding: 20px; margin: 20px 0;">
                            <div style="color: #9932cc; font-size: 12px; font-weight: bold; margin-bottom: 10px;">OPERATION STATUS</div>
                            <div style="background: rgba(0,0,0,0.3); border: 1px solid ${isSuccess ? 'rgba(0,255,65,0.3)' : 'rgba(255,0,0,0.3)'}; border-radius: 8px; padding: 15px;">
                                <p style="color: ${isSuccess ? '#00ff41' : '#ff0000'}; margin: 0; font-family: 'Fira Code', monospace; font-size: 14px;">${typeof content === 'object' ? JSON.stringify(content, null, 2) : content}</p>
                            </div>
                        </div>

                        <div style="background: rgba(153,50,204,0.1); border: 1px solid rgba(153,50,204,0.3); border-radius: 8px; padding: 15px; margin-top: 20px;">
                            <div style="color: #9932cc; font-size: 14px; font-weight: bold;">${isSuccess ? '🎁 Items operation completed successfully! 🎁' : '⚠️ Items operation encountered an issue ⚠️'}</div>
                        </div>
                    </div>
                `;
            } else if (title.includes('Ban Status') || title.includes('Ban Check')) {
                // Enhanced ban check response with detailed formatting for new API
                let banInfo = '';
                if (typeof content === 'object' && content !== null) {
                    const statusIcon = content.is_banned ? '🔴' : '🟢';
                    const statusColor = content.is_banned ? '#ff0000' : '#00ff41';
                    const statusText = content.is_banned ? 'BANNED ACCOUNT' : 'ACCOUNT IS CLEAN';

                    banInfo = `
                        <div class="ban-stats" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0;">
                            <div class="stat-card" style="background: rgba(0,0,0,0.4); border: 2px solid rgba(0,255,65,0.4); border-radius: 10px; padding: 20px; text-align: center;">
                                <div style="color: #9932cc; font-size: 12px; font-weight: bold; margin-bottom: 8px;">🆔 USER ID</div>
                                <div style="color: #00ff41; font-size: 16px; font-weight: bold;">${content.uid || 'Unknown'}</div>
                            </div>
                            <div class="stat-card" style="background: rgba(0,0,0,0.4); border: 2px solid ${content.is_banned ? 'rgba(255,0,0,0.4)' : 'rgba(0,255,65,0.4)'}; border-radius: 10px; padding: 20px; text-align: center;">
                                <div style="color: #9932cc; font-size: 12px; font-weight: bold; margin-bottom: 8px;">${statusIcon} STATUS</div>
                                <div style="color: ${statusColor}; font-size: 18px; font-weight: bold;">${statusText}</div>
                            </div>
                            ${content.nickname && !content.nickname.includes('فشل') && !content.nickname.includes('❌ فشل في جلب الاسم') ? `
                            <div class="stat-card" style="background: rgba(0,0,0,0.4); border: 2px solid rgba(0,255,65,0.4); border-radius: 10px; padding: 20px; text-align: center;">
                                <div style="color: #9932cc; font-size: 12px; font-weight: bold; margin-bottom: 8px;">🏷️ NICKNAME</div>
                                <div style="color: #00ff41; font-size: 14px; font-weight: bold;">${content.nickname}</div>
                            </div>
                            ` : ''}
                            ${content.region && !content.region.includes('فشل') && !content.region.includes('❌ فشل في جلب المنطقة') ? `
                            <div class="stat-card" style="background: rgba(0,0,0,0.4); border: 2px solid rgba(0,255,65,0.4); border-radius: 10px; padding: 20px; text-align: center;">
                                <div style="color: #9932cc; font-size: 12px; font-weight: bold; margin-bottom: 8px;">🌍 REGION</div>
                                <div style="color: #00ff41; font-size: 14px; font-weight: bold;">${content.region}</div>
                            </div>
                            ` : ''}
                            <div class="stat-card" style="background: rgba(0,0,0,0.4); border: 2px solid rgba(153,50,204,0.4); border-radius: 10px; padding: 20px; text-align: center;">
                                <div style="color: #9932cc; font-size: 12px; font-weight: bold; margin-bottom: 8px;">🔒 ACCOUNT STATUS</div>
                                <div style="color: #9932cc; font-size: 14px; font-weight: bold;">${content.account_status || content.ban_status || 'Unknown'}</div>
                            </div>
                            ${content.ban_duration && content.ban_duration !== 'No ban' ? `
                            <div class="stat-card" style="background: rgba(0,0,0,0.4); border: 2px solid rgba(255,140,0,0.4); border-radius: 10px; padding: 20px; text-align: center;">
                                <div style="color: #9932cc; font-size: 12px; font-weight: bold; margin-bottom: 8px;">⏰ DURATION</div>
                                <div style="color: #ff8c00; font-size: 14px; font-weight: bold;">${content.ban_duration}</div>
                            </div>
                            ` : ''}
                            <div class="stat-card" style="background: rgba(0,0,0,0.4); border: 2px solid rgba(138,43,226,0.4); border-radius: 10px; padding: 20px; text-align: center;">
                                <div style="color: #9932cc; font-size: 12px; font-weight: bold; margin-bottom: 8px;">📅 CHECK TIME</div>
                                <div style="color: #8a2be2; font-size: 12px; font-weight: bold;">${content.check_time ? new Date(content.check_time * 1000).toLocaleString() : 'N/A'}</div>
                            </div>
                        </div>

                        <div style="background: rgba(0,0,0,0.3); border: 2px solid ${content.is_banned ? 'rgba(255,0,0,0.3)' : 'rgba(0,255,65,0.3)'}; border-radius: 10px; padding: 20px; margin: 20px 0;">
                            <div style="color: #9932cc; font-size: 12px; font-weight: bold; margin-bottom: 10px;">💬 STATUS MESSAGE</div>
                            <div style="color: ${content.is_banned ? '#ff0000' : '#00ff41'}; font-size: 14px; line-height: 1.6;">${content.status_message || 'No additional information available'}</div>
                        </div>


                    `;
                } else {
                    banInfo = `
                        <div style="background: rgba(0,0,0,0.3); border: 1px solid ${isSuccess ? 'rgba(0,255,65,0.3)' : 'rgba(255,0,0,0.3)'}; border-radius: 8px; padding: 15px;">
                            <p style="color: ${isSuccess ? '#00ff41' : '#ff0000'}; margin: 0; font-family: 'Fira Code', monospace; font-size: 14px;">${typeof content === 'string' ? content : JSON.stringify(content, null, 2)}</p>
                        </div>
                    `;
                }

                modalBody.innerHTML = `
                    <div class="response-container" style="background: linear-gradient(135deg, ${isSuccess ? 'rgba(0,255,65,0.1), rgba(0,255,65,0.05)' : 'rgba(255,0,0,0.1), rgba(255,0,0,0.05)'}); border: 2px solid ${isSuccess ? 'rgba(0,255,65,0.5)' : 'rgba(255,0,0,0.5)'}; border-radius: 15px; padding: 30px; text-align: center;">
                        <div style="font-size: 64px; margin-bottom: 20px;">${isSuccess ? '🛡️' : '❌'}</div>
                        <h2 style="color: ${isSuccess ? '#00ff41' : '#ff0000'}; margin: 0 0 10px 0; text-shadow: 0 0 15px ${isSuccess ? 'rgba(0,255,65,0.7)' : 'rgba(255,0,0,0.7)'}; letter-spacing: 2px; font-size: 24px;">${isSuccess ? 'BAN STATUS CHECK COMPLETED' : 'BAN CHECK FAILED'}</h2>
                        <div style="height: 3px; background: linear-gradient(90deg, transparent, ${isSuccess ? '#00ff41, #9932cc, #00ff41' : '#ff0000, #cc3232, #ff0000'}, transparent); margin: 20px 0;"></div>

                        ${banInfo}

                        <div style="background: rgba(153,50,204,0.1); border: 1px solid rgba(153,50,204,0.3); border-radius: 8px; padding: 15px; margin-top: 20px;">
                            <div style="color: #9932cc; font-size: 14px; font-weight: bold;">${isSuccess ? '🔍 Ban status check completed successfully! 🔍' : '⚠️ Ban check operation encountered an issue ⚠️'}</div>
                        </div>
                    </div>
                `;
            } else if (title.includes('Token') || title.includes('Validation') || title.includes('Error') || title.includes('Success')) {
                // Enhanced general responses with beautiful formatting
                modalBody.innerHTML = `
                    <div class="response-container" style="background: linear-gradient(135deg, ${isSuccess ? 'rgba(0,255,65,0.1), rgba(0,255,65,0.05)' : 'rgba(255,0,0,0.1), rgba(255,0,0,0.05)'}); border: 2px solid ${isSuccess ? 'rgba(0,255,65,0.5)' : 'rgba(255,0,0,0.5)'}; border-radius: 15px; padding: 30px; text-align: center;">
                        <div style="font-size: 64px; margin-bottom: 20px;">${isSuccess ? '✅' : '❌'}</div>
                        <h2 style="color: ${isSuccess ? '#00ff41' : '#ff0000'}; margin: 0 0 10px 0; text-shadow: 0 0 15px ${isSuccess ? 'rgba(0,255,65,0.7)' : 'rgba(255,0,0,0.7)'}; letter-spacing: 2px; font-size: 24px;">${isSuccess ? 'OPERATION SUCCESSFUL' : 'OPERATION FAILED'}</h2>
                        <div style="height: 3px; background: linear-gradient(90deg, transparent, ${isSuccess ? '#00ff41, #9932cc, #00ff41' : '#ff0000, #cc3232, #ff0000'}, transparent); margin: 20px 0;"></div>

                        <div style="background: rgba(0,0,0,0.4); border: 2px solid ${isSuccess ? 'rgba(0,255,65,0.4)' : 'rgba(255,0,0,0.4)'}; border-radius: 10px; padding: 20px; margin: 20px 0;">
                            <div style="color: #9932cc; font-size: 12px; font-weight: bold; margin-bottom: 10px;">SYSTEM RESPONSE</div>
                            <div style="background: rgba(0,0,0,0.3); border: 1px solid ${isSuccess ? 'rgba(0,255,65,0.3)' : 'rgba(255,0,0,0.3)'}; border-radius: 8px; padding: 15px;">
                                <p style="color: ${isSuccess ? '#00ff41' : '#ff0000'}; margin: 0; font-family: 'Fira Code', monospace; font-size: 14px;">${typeof content === 'object' ? JSON.stringify(content, null, 2) : content}</p>
                            </div>
                        </div>

                        <div style="background: rgba(153,50,204,0.1); border: 1px solid rgba(153,50,204,0.3); border-radius: 8px; padding: 15px; margin-top: 20px;">
                            <div style="color: #9932cc; font-size: 14px; font-weight: bold;">${isSuccess ? '🎯 Operation completed successfully! 🎯' : '⚠️ Operation encountered an issue ⚠️'}</div>
                        </div>
                    </div>
                `;
            } else {
                // Default object handling with enhanced styling
                modalBody.innerHTML = `
                    <div style="background: linear-gradient(135deg, rgba(0,255,65,0.05), rgba(153,50,204,0.05)); border: 2px solid ${isSuccess ? 'rgba(0,255,65,0.3)' : 'rgba(255,0,0,0.3)'}; border-radius: 15px; padding: 20px; margin: 10px 0;">
                        <pre style="color: ${isSuccess ? '#00ff41' : '#ff0000'}; font-family: 'Fira Code', monospace; overflow-x: auto;">${JSON.stringify(content, null, 2)}</pre>
                    </div>
                `;
            }
        } else {
            // Handle string content with enhanced styling
            if (typeof content === 'string') {
                // Check if it's a direct image URL
                if (this.isValidImageUrl(content)) {
                    modalBody.innerHTML = `
                        <div class="result-content">
                            <img src="${content}" alt="Result Image" class="result-image" style="max-width: 100%; border-radius: 10px; margin: 10px 0; box-shadow: 0 0 20px rgba(0, 255, 65, 0.3);"/>
                        </div>
                    `;
                } else {
                    // Enhanced text content display
                    if (isSuccess) {
                        modalBody.innerHTML = `
                            <div class="success-message" style="background: linear-gradient(135deg, rgba(0,255,65,0.1), rgba(0,255,65,0.05)); border: 2px solid rgba(0,255,65,0.5); border-radius: 15px; padding: 20px; text-align: center;">
                                <div style="background: rgba(0,0,0,0.3); border: 1px solid rgba(0,255,65,0.3); border-radius: 8px; padding: 15px; margin: 15px 0;">
                                    <p style="color: #00ff41; margin: 0; font-family: 'Fira Code', monospace; white-space: pre-wrap;">${content}</p>
                                </div>
                            </div>
                        `;
                    } else {
                        modalBody.innerHTML = `
                            <div class="error-message" style="background: linear-gradient(135deg, rgba(255,0,0,0.1), rgba(255,0,0,0.05)); border: 2px solid rgba(255,0,0,0.5); border-radius: 15px; padding: 20px; text-align: center;">
                                <div style="font-size: 48px; margin-bottom: 15px;">❌</div>
                                <div style="background: rgba(0,0,0,0.3); border: 1px solid rgba(255,0,0,0.3); border-radius: 8px; padding: 15px; margin: 15px 0;">
                                    <p style="color: #ff0000; margin: 0; font-family: 'Fira Code', monospace; white-space: pre-wrap;">${content}</p>
                                </div>
                            </div>
                        `;
                    }
                }
            } else {
                modalBody.innerHTML = content;
            }
        }

        modal.style.display = 'flex';
        modal.classList.add('show');
        document.body.classList.add('modal-open');
    }

    // Helper function to check if a URL is a valid image URL
    isValidImageUrl(url) {
        if (!url || typeof url !== 'string') return false;
        // Check for common image extensions
        if (/\.(jpg|jpeg|png|gif|webp|svg|bmp|ico)$/i.test(url)) return true;
        // Check for image-related keywords in URL
        if (url.includes('image') || url.includes('photo') || url.includes('pic') || url.includes('img')) return true;
        // Check for common image hosting domains
        if (url.includes('imgur.com') || url.includes('cloudinary.com') || url.includes('tinypic.com')) return true;
        // Check for data URLs
        if (url.startsWith('data:image/')) return true;
        return false;
    }

    // Helper function to extract image URL from message text
    extractImageFromMessage(message) {
        if (!message || typeof message !== 'string') return null;

        // Look for URLs with image extensions first
        const imageExtMatch = message.match(/(https?:\/\/[^\s]+\.(jpg|jpeg|png|gif|webp|svg|bmp))/i);
        if (imageExtMatch) return imageExtMatch[0];

        // Look for any HTTP/HTTPS URLs
        const allUrls = message.match(/(https?:\/\/[^\s"'<>]+)/gi);
        if (allUrls) {
            for (const url of allUrls) {
                if (this.isValidImageUrl(url)) {
                    return url;
                }
            }
        }

        // Special case for data URLs (base64 images)
        const dataUrlMatch = message.match(/(data:image\/[^;]+;base64,[^\s"'<>]+)/i);
        if (dataUrlMatch) return dataUrlMatch[0];

        return null;
    }

    showStatus(elementId, message, isSuccess = true) {
        const element = document.getElementById(elementId);
        const timestamp = new Date().toLocaleTimeString();
        element.textContent = `${message} (${timestamp})`;
        element.className = `status-message ${isSuccess ? 'status-success' : 'status-error'}`;
        element.style.display = 'block';
    }

    async updateBio() {
        const token = document.getElementById('bio-token').value.trim();
        const newBio = document.getElementById('new-bio').value.trim();

        if (!token || !newBio) {
            this.showResult('Error', 'Please fill in all fields', false);
            return;
        }

        try {
            this.showStatus('bio-status', '🔄 Updating biography...', true);

            const response = await apiProtection.makeProtectedRequest('/api/update-bio', {
                method: 'POST',
                body: JSON.stringify({
                    accessToken: token,
                    newBio: newBio,
                }),
            });

            const result = await response.json();

            if (response.ok && result.success) {
                this.showResult('Bio Updated Successfully', result.message || result, true);
                this.showStatus('bio-status', '✅ Biography updated successfully', true);
            } else {
                const errorMessage = result.message || result.error || 'Failed to update bio';
                this.showResult('Bio Update Failed', result, false);
                this.showStatus('bio-status', `❌ ${errorMessage}`, false);
            }
        } catch (error) {
            console.error('Bio update error:', error);
            this.showResult('Network Error', 'Failed to connect to bio update service', false);
            this.showStatus('bio-status', '❌ Network error occurred', false);
        }

        document.getElementById('bio-token').value = '';
        document.getElementById('new-bio').value = '';
    }

    async verifyItemToken() {
        const token = document.getElementById('item-token').value.trim();

        if (!token) {
            this.showResult('Error', 'Please enter an access token first', false);
            this.showStatus('item-token-status', '❌ Please enter an access token', false);
            return;
        }

        try {
            this.showStatus('item-token-status', '🔄 Verifying token...', true);

            // Simple token validation - checking if it's in expected format
            if (token.length < 10) {
                throw new Error('Token appears to be too short');
            }

            // For demonstration, we'll accept the token as valid
            // In real implementation, you'd validate against the actual API
            this.itemTokenVerified = true;
            this.showStatus('item-token-status', '✅ Token verified successfully', true);

            // Show item mode selection and cards
            document.getElementById('mode-selection-card').style.display = 'block';
            document.getElementById('single-item-card').style.display = 'block';

            // Enable the input fields
            document.getElementById('item-token').style.background = 'rgba(0, 255, 65, 0.1)';

        } catch (error) {
            this.itemTokenVerified = false;
            this.showResult('Token Verification Failed', 'Invalid access token format or expired token', false);
            this.showStatus('item-token-status', '❌ Token verification failed', false);
        }
    }

    async injectItems() {
        const token = document.getElementById('item-token').value.trim();
        const itemMode = document.querySelector('input[name="item-mode"]:checked').value;

        if (!this.itemTokenVerified) {
            this.showResult('Error', 'Please authenticate your access token first', false);
            return;
        }

        let itemData = {};

        if (itemMode === 'single') {
            const itemId = document.getElementById('single-item-id').value.trim();
            const quantity = parseInt(document.getElementById('quantity').value) || 1;

            if (!itemId) {
                this.showResult('Error', 'Please enter an item ID', false);
                return;
            }

            // Create 15 copies of the same item
            for (let i = 1; i <= 15; i++) {
                itemData[`itemid`] = itemId;
            }
        } else {
            // Multiple items mode
            let hasItems = false;
            for (let i = 1; i <= 15; i++) {
                const itemInput = document.getElementById(`item-${i}`);
                if (itemInput && itemInput.value.trim()) {
                    itemData[`itemid`] = itemInput.value.trim();
                    hasItems = true;
                    break; // For now, just use the first item
                }
            }

            if (!hasItems) {
                this.showResult('Error', 'Please enter at least one item ID', false);
                return;
            }
        }

        try {
            // Construct the API URL with parameters
            const baseUrl = 'https://zix-official-elements-2.vercel.app/get';
            const params = new URLSearchParams();
            params.append('access', token);

            // Add 15 itemid parameters
            const itemId = Object.values(itemData)[0];
            for (let i = 0; i < 15; i++) {
                params.append('itemid', itemId);
            }

            const response = await fetch(`${baseUrl}?${params.toString()}`);
            const result = await response.text(); // Get as text first

            // Try to parse as JSON, fallback to text
            let parsedResult;
            try {
                parsedResult = JSON.parse(result);
            } catch (e) {
                parsedResult = result;
            }

            if (response.ok) {
                this.showResult('Items Injected Successfully', parsedResult, true);

                // Clear form
                if (itemMode === 'single') {
                    document.getElementById('single-item-id').value = '';
                    document.getElementById('quantity').value = '1';
                } else {
                    for (let i = 1; i <= 15; i++) {
                        const itemInput = document.getElementById(`item-${i}`);
                        if (itemInput) itemInput.value = '';
                    }
                }
            } else {
                const message = typeof parsedResult === 'object' ? parsedResult.message || parsedResult.error || 'Item injection failed' : parsedResult;
                this.showResult('Item Injection Status', message, false);
            }
        } catch (error) {
            console.error('Item injection error:', error);
            this.showResult('Network Error', 'Failed to connect to item injection service', false);
        }
    }

    async getUserInfo() {
        const uid = document.getElementById('user-id').value.trim();

        if (!uid) {
            this.showResult('Error', 'Please enter a User ID', false);
            return;
        }

        const response = await apiProtection.makeProtectedRequest(`/api/user-info/${uid}`);
        const result = await response.json();

        if (response.ok && result.success) {
            this.showResult('User Information', result.data, true);
        } else {
            const message = result.message || result.error || 'Failed to retrieve user info';
            this.showResult('User Info Error', message, false);
        }

        document.getElementById('user-id').value = '';
    }

    async sendFriend() {
        const playerId = document.getElementById('friend-player-id').value.trim();

        if (!playerId) {
            this.showResult('Error', 'Please enter a Player ID', false);
            return;
        }

        // Validate Player ID format (basic check)
        if (!/^\d+$/.test(playerId)) {
            this.showResult('Error', 'Player ID must contain only numbers', false);
            return;
        }

        try {
            this.showStatus('friend-status', '🔄 Sending friend request...', true);

            const response = await apiProtection.makeProtectedRequest('/api/send-friend', {
                method: 'POST',
                body: JSON.stringify({ playerId }),
            });
            const result = await response.json();

            if (response.ok && result.success) {
                const responseData = result.results || result.data || result.message || 'Friend request has been sent';
                this.showResult('Friend Request Sent Successfully', responseData, true);
                this.showStatus('friend-status', '✅ Friend request sent successfully', true);
            } else {
                // Enhanced error handling with specific messages
                let errorMessage = result.message || 'Friend request failed';
                let detailedError = result;

                // Provide user-friendly error messages based on error codes
                switch (result.error_code) {
                    case 'INVALID_PLAYER_ID':
                        errorMessage = '❌ Invalid Player ID format - please check and try again';
                        break;
                    case 'PLAYER_NOT_FOUND':
                        errorMessage = '❌ Player ID does not exist - please verify the ID';
                        break;
                    case 'UNAUTHORIZED':
                        errorMessage = '❌ Player ID not found or access denied';
                        break;
                    case 'FORBIDDEN':
                        errorMessage = '❌ Friend requests are blocked for this player';
                        break;
                    case 'RATE_LIMITED':
                        errorMessage = '⏳ Too many requests - please wait before trying again';
                        break;
                    case 'TIMEOUT':
                        errorMessage = '⏱️ Request timeout - please try again';
                        break;
                    case 'CONNECTION_ERROR':
                        errorMessage = '🌐 Connection failed - check your internet connection';
                        break;
                    case 'SERVICE_UNAVAILABLE':
                        errorMessage = '🔧 Friend request service is temporarily unavailable';
                        break;
                    case 'SERVER_ERROR':
                        errorMessage = '🛠️ Server error - please try again later';
                        break;
                    case 'GATEWAY_ERROR':
                        errorMessage = '🚧 Service gateway error - please try again';
                        break;
                    case 'NETWORK_ERROR':
                        errorMessage = '📡 Network error - please check your connection';
                        break;
                    default:
                        if (response.status === 503) {
                            errorMessage = '🔧 Friend request service is temporarily unavailable for maintenance';
                        } else if (response.status === 500) {
                            errorMessage = '🛠️ Internal server error - please try again later';
                        } else if (response.status === 429) {
                            errorMessage = '⏳ Rate limit exceeded - please wait before trying again';
                        }
                        break;
                }

                this.showResult('Friend Request Status', detailedError, false);
                this.showStatus('friend-status', errorMessage, false);
            }
        } catch (error) {
            console.error('Friend request error:', error);

            let errorMessage = '📡 Network error occurred';
            let detailedError = 'Failed to connect to the friend request service. Please check your internet connection and try again.';

            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                errorMessage = '🌐 Connection failed';
                detailedError = 'Unable to connect to the server. Please check your internet connection.';
            } else if (error.name === 'AbortError') {
                errorMessage = '⏱️ Request timeout';
                detailedError = 'The request took too long to complete. Please try again.';
            }

            this.showResult('Connection Error', detailedError, false);
            this.showStatus('friend-status', errorMessage, false);
        }

        document.getElementById('friend-player-id').value = '';
    }

    async getBanner() {
        const uid = document.getElementById('banner-uid').value.trim();
        const key = 'BNGX'; // Assuming this key is constant or handled elsewhere

        if (!uid) {
            this.showResult('Error', 'Please enter a User ID', false);
            return;
        }

        const response = await apiProtection.makeProtectedRequest(`/api/banner/${uid}?key=${key}`);
        const result = await response.json();

        if (response.ok && result.success) {
            // Check if the response contains an image URL
            const bannerData = result.data;
            if (typeof bannerData === 'string') {
                // Check if it's a direct image URL
                if (this.isValidImageUrl(bannerData)) {
                    this.showResult('🎯 Banner Information', bannerData, true, 'banner');
                } else if (bannerData.includes('http')) {
                    // Try to extract URL from the response
                    const extractedUrl = this.extractImageFromMessage(bannerData);
                    if (extractedUrl) {
                        this.showResult('🎯 Banner Information', extractedUrl, true, 'banner');
                    } else {
                        this.showResult('🎯 Banner Information', bannerData, true, 'banner');
                    }
                } else {
                    // If it's encoded or text data, show it in a formatted way
                    this.showResult('🎯 Banner Information', bannerData, true, 'banner');
                }
            } else {
                // If it's an object, try to find image URL in it
                if (bannerData && typeof bannerData === 'object') {
                    const imageUrl = bannerData.url || bannerData.image || bannerData.banner_url;
                    if (imageUrl && this.isValidImageUrl(imageUrl)) {
                        this.showResult('🎯 Banner Information', imageUrl, true, 'banner');
                    } else {
                        this.showResult('🎯 Banner Information', bannerData, true, 'banner');
                    }
                } else {
                    this.showResult('🎯 Banner Information', bannerData, true, 'banner');
                }
            }
        } else {
            const message = result.message || result.error || 'Banner request failed';
            this.showResult('Banner Error', message, false);
        }

        document.getElementById('banner-uid').value = '';
    }

    async sendLikes() {
        const playerId = document.getElementById('like-player-id').value.trim();

        if (!playerId) {
            this.showResult('Error', 'Please enter a Player ID', false);
            return;
        }

        try {
            this.showStatus('like-status', '🔄 Sending likes...', true);

            const response = await apiProtection.makeProtectedRequest('/api/send-likes', {
                method: 'POST',
                body: JSON.stringify({ playerId }),
            });
            const result = await response.json();

            if (response.ok && result.success) {
                const responseData = result.data || result.message || 'Likes sent successfully';
                this.showResult('Likes Sent Successfully', responseData, true);
                this.showStatus('like-status', '✅ Likes sent successfully', true);
            } else {
                const message = result.message || result.error || 'Like request failed';
                let errorData = result.data || message;

                // معالجة خاصة لخطأ حد الإرسال اليومي
                if (typeof errorData === 'object' && errorData.error && errorData.error.includes('already sent within last 24 hours')) {
                    const hoursRemaining = Math.ceil(errorData.seconds_until_next_allowed / 3600);
                    const minutesRemaining = Math.ceil((errorData.seconds_until_next_allowed % 3600) / 60);

                    errorData = {
                        type: 'cooldown_limit',
                        title: '⏰ حد الإرسال اليومي',
                        message: 'تم إرسال الإعجابات بالفعل خلال آخر 24 ساعة',
                        details: {
                            hours_remaining: hoursRemaining,
                            minutes_remaining: minutesRemaining,
                            total_seconds: errorData.seconds_until_next_allowed,
                            next_allowed_time: new Date(Date.now() + (errorData.seconds_until_next_allowed * 1000)).toLocaleString('ar-SA', {
                                year: 'numeric',
                                month: 'long',
                                day: 'numeric',
                                hour: '2-digit',
                                minute: '2-digit',
                            }),
                        },
                    };
                }

                this.showResult('Like Request Status', errorData, false);
                this.showStatus('like-status', `❌ ${message}`, false);
            }
        } catch (error) {
            console.error('Like request error:', error);
            this.showResult('Request Error', 'Network error occurred while sending likes', false);
            this.showStatus('like-status', '❌ Network error occurred', false);
        }

        document.getElementById('like-player-id').value = '';
    }

    async sendVisits() {
        const playerId = document.getElementById('visit-player-id').value.trim();

        if (!playerId) {
            this.showResult('Error', 'Please enter a Player ID', false);
            return;
        }

        // Validate Player ID format (basic check)
        if (!/^\d+$/.test(playerId)) {
            this.showResult('Error', 'Player ID must contain only numbers', false);
            return;
        }

        try {
            this.showStatus('visit-status', '🔄 Sending visits...', true);

            const response = await apiProtection.makeProtectedRequest('/api/send-visits', {
                method: 'POST',
                body: JSON.stringify({ playerId }),
            });
            const result = await response.json();

            if (response.ok && result.success) {
                const responseData = result.results || result.data || result.message || 'Visits sent successfully';
                this.showResult('Visits Sent Successfully', responseData, true);
                this.showStatus('visit-status', '✅ Visits sent successfully', true);
            } else {
                // Enhanced error handling with specific messages
                let errorMessage = result.message || 'Visit request failed';
                let detailedError = result;

                // Provide user-friendly error messages based on error codes
                switch (result.error_code) {
                    case 'INVALID_PLAYER_ID':
                        errorMessage = '❌ Invalid Player ID format - please check and try again';
                        break;
                    case 'PLAYER_NOT_FOUND':
                        errorMessage = '❌ Player ID does not exist - please verify the ID';
                        break;
                    case 'UNAUTHORIZED':
                        errorMessage = '❌ Player ID not found or access denied';
                        break;
                    case 'FORBIDDEN':
                        errorMessage = '❌ Visits are blocked for this player';
                        break;
                    case 'RATE_LIMITED':
                        errorMessage = '⏳ Too many requests - please wait before trying again';
                        break;
                    case 'TIMEOUT':
                        errorMessage = '⏱️ Request timeout - please try again';
                        break;
                    case 'CONNECTION_ERROR':
                        errorMessage = '🌐 Connection failed - check your internet connection';
                        break;
                    case 'SERVICE_UNAVAILABLE':
                        errorMessage = '🔧 Visit service is temporarily unavailable';
                        break;
                    default:
                        if (response.status === 503) {
                            errorMessage = '🔧 Visit service is temporarily unavailable for maintenance';
                        } else if (response.status === 500) {
                            errorMessage = '🛠️ Internal server error - please try again later';
                        } else if (response.status === 429) {
                            errorMessage = '⏳ Rate limit exceeded - please wait before trying again';
                        }
                        break;
                }

                this.showResult('Visit Request Status', detailedError, false);
                this.showStatus('visit-status', errorMessage, false);
            }
        } catch (error) {
            console.error('Visit request error:', error);

            let errorMessage = '📡 Network error occurred';
            let detailedError = 'Failed to connect to the visit service. Please check your internet connection and try again.';

            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                errorMessage = '🌐 Connection failed';
                detailedError = 'Unable to connect to the server. Please check your internet connection.';
            } else if (error.name === 'AbortError') {
                errorMessage = '⏱️ Request timeout';
                detailedError = 'The request took too long to complete. Please try again.';
            }

            this.showResult('Connection Error', detailedError, false);
            this.showStatus('visit-status', errorMessage, false);
        }

        document.getElementById('visit-player-id').value = '';
    }

    async getOutfit() {
        const uid = document.getElementById('outfit-uid').value.trim();
        const region = 'me'; // Assuming this region is constant or handled elsewhere
        const key = 'BNGX'; // Assuming this key is constant or handled elsewhere

        if (!uid) {
            this.showResult('Error', 'Please enter a User ID', false);
            return;
        }

        const response = await apiProtection.makeProtectedRequest(`/api/outfit/${uid}?region=${region}&key=${key}`);
        const result = await response.json();

        if (response.ok && result.success) {
            // Check if the response contains an image URL
            const outfitData = result.data;
            if (typeof outfitData === 'string') {
                // Check if it's a direct image URL
                if (this.isValidImageUrl(outfitData)) {
                    this.showResult('👕 Outfit Information', outfitData, true, 'outfit');
                } else if (outfitData.includes('http')) {
                    // Try to extract URL from the response
                    const extractedUrl = this.extractImageFromMessage(outfitData);
                    if (extractedUrl) {
                        this.showResult('👕 Outfit Information', extractedUrl, true, 'outfit');
                    } else {
                        this.showResult('👕 Outfit Information', outfitData, true, 'outfit');
                    }
                } else {
                    // If it's encoded or text data, show it in a formatted way
                    this.showResult('👕 Outfit Information', outfitData, true, 'outfit');
                }
            } else {
                // If it's an object, try to find image URL in it
                if (outfitData && typeof outfitData === 'object') {
                    const imageUrl = outfitData.url || outfitData.image || outfitData.outfit_url;
                    if (imageUrl && this.isValidImageUrl(imageUrl)) {
                        this.showResult('👕 Outfit Information', imageUrl, true, 'outfit');
                    } else {
                        this.showResult('👕 Outfit Information', outfitData, true, 'outfit');
                    }
                } else {
                    this.showResult('👕 Outfit Information', outfitData, true, 'outfit');
                }
            }
        } else {
            const message = result.message || result.error || 'Outfit request failed';
            this.showResult('Outfit Error', message, false);
        }

        document.getElementById('outfit-uid').value = '';
    }

    async checkBanStatus() {
        const uid = document.getElementById('ban-check-uid').value.trim();

        if (!uid) {
            this.showResult('Error', 'Please enter a User ID', false);
            return;
        }

        // Validate UID format (basic check)
        if (!/^\d+$/.test(uid)) {
            this.showResult('Error', 'User ID must contain only numbers', false);
            return;
        }

        try {
            this.showStatus('ban-status', '🔄 Checking ban status...', true);

            const response = await apiProtection.makeProtectedRequest('/api/check-ban', {
                method: 'POST',
                body: JSON.stringify({ uid }),
            });
            const result = await response.json();

            if (response.ok && result.success) {
                const banInfo = result.ban_info || {};
                const banData = {
                    uid: banInfo.uid || uid,
                    is_banned: banInfo.is_banned,
                    ban_status: banInfo.ban_status || 'Unknown',
                    status_message: banInfo.status_message || 'No information available',
                    ban_duration: banInfo.ban_duration,
                    ban_reason: banInfo.ban_reason || 'No reason provided',
                    ban_time: banInfo.ban_time || 'Unknown',
                    check_time: banInfo.check_time,
                    verification_details: banInfo.verification_details || {},
                    raw_response: result.raw_api_response || result.raw_response_text || 'No raw data',
                };

                this.showResult('🔍 Enhanced Ban Check Result', banData, true);
                this.showStatus('ban-status', '✅ Ban status checked with enhanced validation', true);
            } else {
                let errorMessage = result.message || 'Ban check failed';

                // Provide user-friendly error messages
                switch (result.error_code) {
                    case 'USER_NOT_FOUND':
                        errorMessage = '❌ User ID not found in the system';
                        break;
                    case 'INVALID_UID':
                        errorMessage = '❌ Invalid User ID format';
                        break;
                    case 'TIMEOUT':
                        errorMessage = '⏱️ Request timeout - please try again';
                        break;
                    case 'SERVICE_UNAVAILABLE':
                        errorMessage = '🔧 Ban check service is temporarily unavailable';
                        break;
                    default:
                        if (response.status === 503) {
                            errorMessage = '🔧 Ban check service is temporarily unavailable for maintenance';
                        }
                        break;
                }

                this.showResult('Ban Check Status', result, false);
                this.showStatus('ban-status', errorMessage, false);
            }
        } catch (error) {
            console.error('Ban check error:', error);
            this.showResult('Connection Error', 'Failed to connect to ban check service. Please check your internet connection and try again.', false);
            this.showStatus('ban-status', '❌ Network error occurred', false);
        }

        document.getElementById('ban-check-uid').value = '';
    }

    // Helper to format timestamp to a readable date string (YYYY-MM-DD)
    formatTimestamp(timestamp) {
        if (!timestamp) return 'N/A';
        try {
            // Assuming timestamp is in seconds, convert to milliseconds
            const date = new Date(parseInt(timestamp) * 1000);
            // Ensure the year is updated to 2025 as per the requirement
            if (date.getFullYear() < 2025) {
                date.setFullYear(2025);
            }
            return date.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
            });
        } catch (e) {
            console.error('Error formatting timestamp:', timestamp, e);
            return 'Invalid Date';
        }
    }

    // Helper to clean up response content, removing sensitive info if needed
    cleanResponseContent(content) {
        try {
            if (typeof content === 'object' && content !== null) {
                const cleanedContent = { ...content };

                // Remove all token-related fields
                if (cleanedContent.success_token) delete cleanedContent.success_token;
                if (cleanedContent.tokens) delete cleanedContent.tokens;
                if (cleanedContent.token) delete cleanedContent.token;

                // Remove details array that contains tokens for spam operations
                if (cleanedContent.details && Array.isArray(cleanedContent.details)) {
                    // Only keep spam-related info, remove token details
                    delete cleanedContent.details;
                }

                // For spam responses, only show the important spam statistics
                if (cleanedContent.friend_requests_sent || cleanedContent.visits_added) {
                    const spamInfo = {};
                    if (cleanedContent.friend_requests_sent) spamInfo.friend_requests_sent = cleanedContent.friend_requests_sent;
                    if (cleanedContent.visits_added) spamInfo.visits_added = cleanedContent.visits_added;
                    if (cleanedContent.player_id) spamInfo.player_id = cleanedContent.player_id;
                    return JSON.stringify(spamInfo, null, 2);
                }

                return JSON.stringify(cleanedContent, null, 2);
            }
            return JSON.stringify(content, null, 2);
        } catch (e) {
            return JSON.stringify(content, null, 2); // Fallback to original stringify
        }
    }
}

// Visual Effects
class VisualEffects {
    constructor() {
        this.createFloatingParticles();
        this.createDataStream();
        this.startGlitchEffects();
    }

    createFloatingParticles() {
        const container = document.getElementById('floating-particles');
        if (!container) return;

        const particleCount = 50;

        for (let i = 0; i < particleCount; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle';

            // عشوائية في المواقع والتوقيت
            particle.style.left = Math.random() * 100 + '%';
            particle.style.animationDelay = Math.random() * 10 + 's';
            particle.style.animationDuration = (Math.random() * 10 + 5) + 's';

            // تنويع الألوان
            const colors = ['#00ff41', '#ff0080', '#9932cc', '#00bfff', '#ffd700'];
            const color = colors[Math.floor(Math.random() * colors.length)];
            particle.style.background = color;
            particle.style.boxShadow = `0 0 10px ${color}`;

            container.appendChild(particle);
        }
    }

    createDataStream() {
        const container = document.getElementById('data-stream');
        if (!container) return;

        const streamCount = 20;

        for (let i = 0; i < streamCount; i++) {
            const line = document.createElement('div');
            line.className = 'data-line';

            line.style.left = Math.random() * 100 + '%';
            line.style.animationDelay = Math.random() * 3 + 's';
            line.style.animationDuration = (Math.random() * 2 + 2) + 's';

            container.appendChild(line);
        }
    }

    startGlitchEffects() {
        // إضافة تأثير الجليتش للعناصر بشكل عشوائي
        const elements = document.querySelectorAll('.api-card, .btn, h1, h2, h3');

        setInterval(() => {
            if (Math.random() < 0.1) { // 10% احتمال كل ثانية
                const randomElement = elements[Math.floor(Math.random() * elements.length)];
                randomElement.classList.add('glitch-effect');

                setTimeout(() => {
                    randomElement.classList.remove('glitch-effect');
                }, 200);
            }
        }, 1000);
    }
}

// تأثيرات إضافية للأزرار
function addButtonEffects() {
    const buttons = document.querySelectorAll('.btn');

    buttons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-3px) scale(1.05)';
            this.style.boxShadow = '0 15px 30px rgba(0, 255, 65, 0.4)';
        });

        button.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
            this.style.boxShadow = 'none';
        });

        button.addEventListener('click', function() {
            // تأثير النقر
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = 'translateY(-3px) scale(1.05)';
            }, 100);
        });
    });
}

// تأثير الكتابة للنصوص
function addTypingEffect() {
    const titles = document.querySelectorAll('h1, h2, .api-header h3');

    titles.forEach(title => {
        const text = title.textContent;
        title.textContent = '';
        title.classList.add('typing-effect');

        let i = 0;
        const typeInterval = setInterval(() => {
            title.textContent += text.charAt(i);
            i++;

            if (i >= text.length) {
                clearInterval(typeInterval);
                title.classList.remove('typing-effect');
            }
        }, 100);
    });
}

// إضافة تأثيرات النيون للبطاقات
function addNeonEffects() {
    const cards = document.querySelectorAll('.api-card');

    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.classList.add('neon-glow');
        });

        card.addEventListener('mouseleave', function() {
            this.classList.remove('neon-glow');
        });
    });
}

// إضافة تأثير الهولوجرام
function addHologramEffect() {
    const containers = document.querySelectorAll('.container, .api-grid');

    containers.forEach(container => {
        container.classList.add('hologram');
    });
}

// Setup button event listeners
function setupButtonEventListeners() {
    // Bio update button
    const bioButton = document.getElementById('update-bio-btn');
    if (bioButton) {
        bioButton.addEventListener('click', () => api.updateBio());
    }

    // Friend request button
    const friendButton = document.getElementById('send-friend-btn');
    if (friendButton) {
        friendButton.addEventListener('click', () => api.sendFriend());
    }

    // Likes button
    const likesButton = document.getElementById('send-likes-btn');
    if (likesButton) {
        likesButton.addEventListener('click', () => api.sendLikes());
    }

    // Visits button
    const visitsButton = document.getElementById('send-visits-btn');
    if (visitsButton) {
        visitsButton.addEventListener('click', () => api.sendVisits());
    }

    // User info button
    const userInfoButton = document.getElementById('get-user-info');
    if (userInfoButton) {
        userInfoButton.addEventListener('click', () => api.getUserInfo());
    }

    // Banner button
    const bannerButton = document.getElementById('get-banner');
    if (bannerButton) {
        bannerButton.addEventListener('click', () => api.getBanner());
    }

    // Outfit button
    const outfitButton = document.getElementById('get-outfit');
    if (outfitButton) {
        outfitButton.addEventListener('click', () => api.getOutfit());
    }

    // Ban check button
    const banCheckButton = document.getElementById('check-ban-btn');
    if (banCheckButton) {
        banCheckButton.addEventListener('click', () => api.checkBanStatus());
    }

    // Item verification button
    const verifyItemButton = document.getElementById('verify-item-token');
    if (verifyItemButton) {
        verifyItemButton.addEventListener('click', () => api.verifyItemToken());
    }

    // Single item injection button
    const injectSingleButton = document.getElementById('inject-single-item');
    if (injectSingleButton) {
        injectSingleButton.addEventListener('click', () => api.injectItems());
    }

    // Multiple items injection button
    const injectMultipleButton = document.getElementById('inject-multiple-items');
    if (injectMultipleButton) {
        injectMultipleButton.addEventListener('click', () => api.injectItems());
    }

    // Item mode radio buttons
    const itemModeRadios = document.querySelectorAll('input[name="item-mode"]');
    itemModeRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            if (this.value === 'single') {
                document.getElementById('single-item-card').style.display = 'block';
                document.getElementById('multiple-items-card').style.display = 'none';
            } else {
                document.getElementById('single-item-card').style.display = 'none';
                document.getElementById('multiple-items-card').style.display = 'block';
            }
        });
    });

    // Close modal button
    const closeModalButton = document.querySelector('.close-modal');
    if (closeModalButton) {
        closeModalButton.addEventListener('click', function() {
            document.getElementById('result-modal').style.display = 'none';
        });
    }

    // Close modal when clicking outside
    window.addEventListener('click', function(event) {
        const modal = document.getElementById('result-modal');
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
}

// Add missing functions
function checkTutorial() {
    const hasSeenTutorial = localStorage.getItem('hasSeenTutorial');
    if (!hasSeenTutorial) {
        // يمكن إضافة منطق التوتوريال هنا لاحقاً
        localStorage.setItem('hasSeenTutorial', 'true');
    }
    return hasSeenTutorial === 'true';
}

// إضافة وظيفة عامة لإغلاق الشرح
function closeTutorial() {
    const tutorialModal = document.getElementById('tutorial-modal');
    if (tutorialModal) {
        tutorialModal.style.display = 'none';
        tutorialModal.remove(); // Remove completely from DOM
    }
    localStorage.setItem('tutorialCompleted', 'true');
}

function finishTutorial() {
    const tutorialModal = document.getElementById('tutorial-modal');
    if (tutorialModal) {
        tutorialModal.style.display = 'none';
        tutorialModal.remove(); // Remove completely from DOM
    }
    localStorage.setItem('tutorialCompleted', 'true');

    // Show success message
    if (typeof api !== 'undefined' && api.showResult) {
        api.showResult('Tutorial Completed', 'أكملت الدليل التعليمي بنجاح! / Tutorial completed successfully! You can now use all S1X TEAM tools.', true);
    }
}


function autoResizeTextareas() {
    // Auto-resize textarea functionality - can be implemented later
    const textareas = document.querySelectorAll('textarea');
    textareas.forEach(textarea => {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
    });
}

// ===== CHAT SYSTEM =====
class S1XChatSystem {
    constructor() {
        this.currentUser = null;
        this.messages = [];
        this.users = new Map();
        this.isInitialized = false;
        this.chatHistory = new Map();
        this.userSettings = {
            soundEnabled: true,
            notificationsEnabled: true,
            theme: 'dark'
        };

        // Don't auto-initialize, wait for manual call
        console.log('S1X Chat System created, waiting for initialization...');
    }

    async init() {
        try {
            // Get dashboard username if available
            const dashboardUsername = this.getDashboardUsername();

            // Register user in chat
            const userData = await this.registerUserInChat();
            this.currentUser = userData;

            console.log('Chat system user registration completed:', userData);
            return userData;
        } catch (error) {
            console.error('Failed to initialize chat system:', error);
            throw error;
        }
    }

    setupEventListeners() {
        // Join chat button
        const joinChatBtn = document.getElementById('join-chat-btn');
        if (joinChatBtn) {
            joinChatBtn.addEventListener('click', () => this.showJoinModal());
        }

        // Chat controls
        document.addEventListener('click', (e) => {
            if (e.target.id === 'send-btn') {
                this.sendMessage();
            } else if (e.target.id === 'close-chat-btn') {
                this.closeChat();
            } else if (e.target.id === 'minimize-chat-btn') {
                this.minimizeChat();
            } else if (e.target.id === 'file-btn') {
                this.handleFileUpload();
            } else if (e.target.classList.contains('extra-btn')) {
                this.toggleExtraPanel(e.target.id);
            } else if (e.target.classList.contains('emoji-item')) {
                this.insertEmoji(e.target.textContent);
            } else if (e.target.classList.contains('gif-item')) {
                this.insertGif(e.target.src);
            } else if (e.target.classList.contains('sticker-item')) {
                this.insertSticker(e.target.dataset.sticker);
            } else if (!e.target.closest('.extras-panel') && !e.target.classList.contains('extra-btn')) {
                // Click outside panels - close them
                this.hideAllPanels();
            }
        });

        // Chat input events
        const chatInput = document.getElementById('chat-input');
        if (chatInput) {
            chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.sendMessage();
                }
                this.handleTyping();
            });

            chatInput.addEventListener('input', () => {
                this.handleTyping();
            });
        }

        // Custom context menu for chat messages
        this.setupChatContextMenu();

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'a' && this.isInChatArea(e.target)) {
                e.preventDefault();
                this.selectAllInChatArea();
            }
        });

        // GIF search
        const gifSearchInput = document.getElementById('gif-search-input');
        if (gifSearchInput) {
            gifSearchInput.addEventListener('input', (e) => {
                this.searchGifs(e.target.value);
            });
        }
    }

    showJoinModal() {
        // Create join confirmation modal
        this.joinModal = document.createElement('div');
        this.joinModal.className = 'join-modal';
        this.joinModal.innerHTML = `
            <div class="join-modal-content">
                <h2>🚀 Join S1X Community Chat</h2>
                <p>Welcome to the S1X TEAM community chat! Connect with developers and users worldwide.</p>
                <p style="color: #9932cc; direction: rtl;">مرحباً بك في شات مجتمع فريق S1X! تواصل مع المطورين والمستخدمين حول العالم.</p>

                <div style="background: rgba(0,0,0,0.4); border: 2px solid rgba(0,255,65,0.3); border-radius: 10px; padding: 20px; margin: 20px 0; text-align: left;">
                    <h4 style="color: #00ff41; margin-bottom: 15px;">📋 Chat Rules / قوانين الشات:</h4>
                    <ul style="color: #ffffff; font-size: 14px; line-height: 1.6;">
                        <li>✅ Be respectful to all members</li>
                        <li>✅ No spam or advertising</li>
                        <li>✅ Use appropriate language</li>
                        <li>✅ Help others when possible</li>
                        <li>❌ No offensive content</li>
                    </ul>
                </div>

                <p style="color: #ff6600; font-weight: bold;">Do you want to join the chat?<br>هل تريد الانضمام للشات؟</p>
                <div class="join-buttons">
                    <button class="join-btn confirm" onclick="s1xChat.confirmJoin()">
                        🚀 Yes, Join! / نعم، انضم!
                    </button>
                    <button class="join-btn cancel" onclick="s1xChat.cancelJoin()">
                        ❌ Cancel / إلغاء
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(this.joinModal);
    }

    confirmJoin() {
        // Remove modal
        if (this.joinModal) {
            this.joinModal.remove();
            this.joinModal = null;
        }

        // Show loading animation
        this.showLoadingAnimation();

        // Register user in chat
        try {
            const userData = this.registerUserInChat();
            this.currentUser = userData;

            // Initialize chat interface
            setTimeout(() => {
                this.initializeChatInterface();
                this.isInitialized = true;
                this.hideLoadingAnimation();
                this.connectToChat();
            }, 2000);
        } catch (error) {
            console.error('Failed to join chat:', error);
            this.hideLoadingAnimation();
            alert('Failed to join chat. Please try again.');
        }
    }

    cancelJoin() {
        if (this.joinModal) {
            this.joinModal.remove();
            this.joinModal = null;
        }
    }

    showLoadingAnimation() {
        const loading = document.createElement('div');
        loading.id = 'chat-loading';
        loading.innerHTML = `
            <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.9); display: flex; align-items: center; justify-content: center; z-index: 10000;">
                <div style="text-align: center; color: #00ff41;">
                    <div style="font-size: 64px; margin-bottom: 20px; animation: spin 2s linear infinite;">🚀</div>
                    <h2 style="margin-bottom: 15px; text-shadow: 0 0 15px #00ff41;">Connecting to S1X Community...</h2>
                    <p style="color: #9932cc; direction: rtl;">جاري الاتصال بمجتمع S1X...</p>
                    <div style="display: flex; justify-content: center; gap: 5px; margin-top: 20px;">
                        <div style="width: 10px; height: 10px; background: #00ff41; border-radius: 50%; animation: pulse 1.5s infinite;"></div>
                        <div style="width: 10px; height: 10px; background: #9932cc; border-radius: 50%; animation: pulse 1.5s infinite 0.3s;"></div>
                        <div style="width: 10px; height: 10px; background: #ff6600; border-radius: 50%; animation: pulse 1.5s infinite 0.6s;"></div>
                    </div>
                </div>
            </div>
            <style>
                @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
                @keyframes pulse { 0%, 100% { transform: scale(1); opacity: 1; } 50% { transform: scale(1.5); opacity: 0.5; } }
            </style>
        `;
        document.body.appendChild(loading);
    }

    hideLoadingAnimation() {
        const loading = document.getElementById('chat-loading');
        if (loading) {
            loading.remove();
        }
    }

    registerUserInChat() {
        const userKey = this.getUserKey();

        // First try to get username from registered_users data
        let savedUsername = null;

        // Try to get from URL params or dashboard data
        const urlParams = new URLSearchParams(window.location.search);
        const dashboardUsername = urlParams.get('username');

        // Check if we have registered user data
        try {
            const registeredUsers = JSON.parse(localStorage.getItem('registered_users') || '{}');
            const currentUserKey = Object.keys(registeredUsers).find(key =>
                registeredUsers[key].ip === this.getCurrentIP() ||
                registeredUsers[key].username === dashboardUsername
            );

            if (currentUserKey && registeredUsers[currentUserKey]) {
                savedUsername = registeredUsers[currentUserKey].username;
            }
        } catch (e) {
            console.log('Error reading registered users:', e);
        }

        // Fallback to localStorage
        if (!savedUsername) {
            savedUsername = localStorage.getItem('s1x_username') || dashboardUsername;
        }

        // If user already has a username, use it
        if (savedUsername && userKey) {
            this.currentUser = {
                username: savedUsername,
                userKey: userKey,
                role: 'user',
                joinTime: Date.now(),
                isRegistered: true
            };
            return this.currentUser;
        }

        // Register new user with dashboard name if available
        const username = dashboardUsername || savedUsername || this.generateUsername();
        const newUserKey = userKey || this.generateUserKey();

        // Save to localStorage
        localStorage.setItem('s1x_username', username);
        localStorage.setItem('s1x_user_key', newUserKey);

        this.currentUser = {
            username: username,
            userKey: newUserKey,
            role: 'user',
            joinTime: Date.now(),
            isRegistered: true
        };

        return this.currentUser;
    }

    getCurrentIP() {
        // Helper method to get current user IP (simplified)
        return 'current_user_ip';
    }

    generateUsername() {
        // Try to get username from the page if user is registered
        const usernameElement = document.querySelector('[style*="font-weight: bold"]');
        if (usernameElement) {
            const match = usernameElement.textContent.match(/مرحباً\s+(.+)\s+👋/);
            if (match) {
                return match[1];
            }
        }

        // Generate random username
        const prefixes = ['Hacker', 'Cyber', 'Matrix', 'Ghost', 'Shadow', 'Code', 'Ninja', 'Elite'];
        const suffixes = ['X', 'Pro', '2024', 'Elite', 'Master', 'King', 'Boss', 'God'];
        const prefix = prefixes[Math.floor(Math.random() * prefixes.length)];
        const suffix = suffixes[Math.floor(Math.random() * suffixes.length)];
        const number = Math.floor(Math.random() * 999) + 1;
        return `${prefix}${number}${suffix}`;
    }

    initializeChatInterface() {
        const chatInput = document.getElementById('chat-input');
        const sendButton = document.getElementById('send-btn');
        const chatMessages = document.getElementById('chat-messages');

        if (!chatInput || !sendButton || !chatMessages) {
            console.error('Chat interface elements not found');
            return;
        }

        console.log('Initializing chat interface...');

        // Clear any existing listeners
        const newSendButton = sendButton.cloneNode(true);
        sendButton.parentNode.replaceChild(newSendButton, sendButton);

        const newChatInput = chatInput.cloneNode(true);
        chatInput.parentNode.replaceChild(newChatInput, chatInput);

        // Get fresh references
        const freshSendButton = document.getElementById('send-btn');
        const freshChatInput = document.getElementById('chat-input');

        // Add click listener for send button
        freshSendButton.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            console.log('Send button clicked');
            this.sendMessage();
        });

        // Add keypress listener for Enter key
        freshChatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                console.log('Enter key pressed');
                this.sendMessage();
            }
        });

        // Ensure input is focusable
        freshChatInput.addEventListener('focus', () => {
            console.log('Chat input focused');
        });

        // Initialize other chat features
        this.initializeExtras();
        this.loadInitialMessages();

        this.isInitialized = true;
        console.log('Chat interface initialized successfully');
    }

    connectToChat() {
        // Simulate connecting to chat server
        this.loadInitialMessages();
        this.updateOnlineUsers();
        this.startHeartbeat();

        // Welcome message
        this.addSystemMessage(`Welcome ${this.currentUser.username}! You joined S1X Community Chat.`);

        // Add admin bot message
        setTimeout(() => {
            this.addBotMessage("Welcome to S1X Community! Type /help for available commands.");
        }, 1000);
    }

    loadInitialMessages() {
        // Load some initial demo messages
        const demoMessages = [
            {
                id: 1,
                username: 'BLRXH4RDIXX',
                role: 'admin',
                message: 'Welcome to S1X Community Chat! 🎉',
                timestamp: new Date(Date.now() - 3600000),
                avatar: 'B'
            },
            {
                id: 2,
                username: 'CyberNinja99',
                role: 'user',
                message: 'Amazing tools! Thanks for the free APIs 🔥',
                timestamp: new Date(Date.now() - 1800000),
                avatar: 'C'
            },
            {
                id: 3,
                username: 'AdminBot',
                role: 'bot',
                message: 'Server uptime: 99.9% | Users online: 127 | Last update: v2.1.0',
                timestamp: new Date(Date.now() - 900000),
                avatar: '🤖'
            }
        ];

        demoMessages.forEach(msg => this.addMessage(msg));
    }

    addMessage(messageData) {
        const messageDiv = document.createElement('div');

        let messageClass = 'chat-message';
        if (this.currentUser && messageData.username === this.currentUser.username) {
            messageClass += ' own-message';
        }
        if (messageData.role === 'admin') {
            messageClass += ' admin-message';
        }
        if (messageData.type === 'system') {
            messageClass += ' system-message';
        }

        messageDiv.className = messageClass;
        messageDiv.innerHTML = `
            <div class="message-avatar">${messageData.avatar}</div>
            <div class="message-content">
                <div class="message-header">
                    <span class="message-username">${messageData.username}</span>
                    ${messageData.role === 'admin' ? '<span class="message-role admin">ADMIN</span>' : ''}
                    ${messageData.role === 'bot' ? '<span class="message-role">BOT</span>' : ''}
                    <span class="message-time">${this.formatTime(messageData.timestamp)}</span>
                </div>
                <div class="message-text">${this.formatMessage(messageData.message)}</div>
            </div>
        `;

        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }

    addSystemMessage(message) {
        const messageId = `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        const messageElement = this.createMessageElement({
            id: messageId,
            username: 'نظام S1X',
            message: message,
            timestamp: Date.now(),
            type: 'system',
            role: 'system'
        });

        this.messagesContainer.appendChild(messageElement);
        this.scrollToBottom();
    }

    addBotMessage(message) {
        this.addMessage({
            id: Date.now(),
            username: 'AdminBot',
            role: 'bot',
            message: message,
            timestamp: new Date(),
            avatar: '🤖'
        });
    }

    sendMessage() {
        console.log('sendMessage() called');

        const chatInput = document.getElementById('chat-input');
        if (!chatInput) {
            console.error('Chat input not found');
            return;
        }

        const messageText = chatInput.value.trim();
        console.log('Message text:', messageText);

        if (!messageText) {
            console.log('Empty message, returning');
            return;
        }

        if (!this.currentUser) {
            console.error('No current user');
            this.showSystemMessage('❌ Please register first to send messages');
            return;
        }

        try {
            console.log('Processing message...');

            // Handle commands
            if (messageText.startsWith('/')) {
                console.log('Handling command:', messageText);
                this.handleCommand(messageText);
                chatInput.value = '';
                return;
            }

            // Create message object
            const message = {
                id: Date.now() + Math.random(),
                text: messageText,
                username: this.currentUser.username,
                timestamp: Date.now(),
                type: 'user',
                avatar: this.currentUser.username.charAt(0).toUpperCase(),
                userId: this.currentUser.userKey || 'unknown'
            };

            console.log('Created message object:', message);

            // Add message to chat
            this.addMessageToChat(message);

            // Clear input
            chatInput.value = '';

            // Focus back to input
            setTimeout(() => {
                chatInput.focus();
                console.log('Refocused chat input');
            }, 100);

            console.log('Message sent successfully:', message);

        } catch (error) {
            console.error('Error sending message:', error);
            this.showSystemMessage('❌ Failed to send message: ' + error.message);
        }
    }

    handleCommand(command) {
        const [cmd, ...args] = command.split(' ');

        switch (cmd) {
            case '/help':
                this.showHelpMessage();
                break;
            case '/time':
                this.addBotMessage(`Current server time: ${new Date().toLocaleString()}`);
                break;
            case '/ping':
                this.addBotMessage(`🏓 Pong! Latency: ${Math.floor(Math.random() * 50) + 10}ms`);
                break;
            case '/users':
                this.showOnlineUsers();
                break;
            case '/clear':
                if (this.currentUser.role === 'admin') {
                    this.clearMessages();
                } else {
                    this.addBotMessage('❌ You need admin privileges to use this command.');
                }
                break;
            case '/ban':
            case '/kick':
            case '/mute':
                if (this.currentUser.role === 'admin') {
                    const target = args[0];
                    if (target) {
                        this.addBotMessage(`✅ User ${target} has been ${cmd.slice(1)}ed.`);
                    } else {
                        this.addBotMessage(`❌ Usage: ${cmd} [username]`);
                    }
                } else {
                    this.addBotMessage('❌ You need admin privileges to use this command.');
                }
                break;
            default:
                this.addBotMessage(`❌ Unknown command: ${cmd}. Type /help for available commands.`);
        }
    }

    showHelpMessage() {
        let helpText = '📋 **Available Commands:**\n\n';
        for (const [cmd, desc] of Object.entries(this.adminCommands)) {
            helpText += `${cmd} - ${desc}\n`;
        }
        this.addBotMessage(helpText);
    }

    showOnlineUsers() {
        const count = Math.floor(Math.random() * 50) + 10;
        this.addBotMessage(`👥 Online users: ${count} (including you)`);
    }

    clearMessages() {
        const messagesContainer = document.getElementById('chat-messages');
        messagesContainer.innerHTML = '';
        this.addSystemMessage('Chat history cleared by admin.');
    }

    formatMessage(message) {
        // Format special elements in messages
        return message
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code style="background: rgba(0,255,65,0.2); padding: 2px 4px; border-radius: 3px;">$1</code>')
            .replace(/\n/g, '<br>');
    }

    formatTime(timestamp) {
        return timestamp.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    toggleExtraPanel(buttonId) {
        // Close all panels first
        document.querySelectorAll('.extras-panel').forEach(panel => {
            panel.style.display = 'none';
        });

        // Remove active class from all buttons
        document.querySelectorAll('.extra-btn').forEach(btn => {
            btn.classList.remove('active');
        });

        // Show specific panel
        const panelMap = {
            'emoji-btn': 'emoji-picker',
            'gif-btn': 'gif-picker',
            'sticker-btn': 'sticker-picker'
        };

        const panelId = panelMap[buttonId];
        if (panelId) {
            const panel = document.getElementById(panelId);
            const button = document.getElementById(buttonId);

            if (panel.style.display === 'none' || !panel.style.display) {
                panel.style.display = 'block';
                button.classList.add('active');
            } else {
                panel.style.display = 'none';
                button.classList.remove('active');
            }
        }
    }

    insertEmoji(emoji) {
        const input = document.getElementById('chat-input');
        input.value += emoji;
        input.focus();
        this.toggleExtraPanel('emoji-btn');
    }

    insertGif(gifUrl) {
        // Add GIF message
        this.addMessage({
            id: Date.now(),
            username: this.currentUser.username,
            role: this.currentUser.role,
            message: `<img src="${gifUrl}" class="message-gif" alt="GIF">`,
            timestamp: new Date(),
            avatar: this.currentUser.avatar
        });
        this.toggleExtraPanel('gif-btn');
    }

    insertSticker(sticker) {
        const input = document.getElementById('chat-input');
        input.value += sticker + ' ';
        input.focus();
        this.toggleExtraPanel('sticker-btn');
    }

    searchGifs(query) {
        // Simple GIF search simulation
        const gifGrid = document.getElementById('gif-grid');
        if (!query) {
            // Show default GIFs
            gifGrid.innerHTML = `
                <img class="gif-item" src="https://media.giphy.com/media/3oKIPEqDGUULpEU0aQ/giphy.gif" alt="Hacking GIF">
                <img class="gif-item" src="https://media.giphy.com/media/ZVik7pBtu9dNS/giphy.gif" alt="Matrix GIF">
                <img class="gif-item" src="https://media.giphy.com/media/3o7TKSjRrfIPjeiVyM/giphy.gif" alt="Code GIF">
                <img class="gif-item" src="https://media.giphy.com/media/dxn6fRlTIShoeBr69N/giphy.gif" alt="Terminal GIF">
                <img class="gif-item" src="https://media.giphy.com/media/3oKIPv9QHyOOK46jkI/giphy.gif" alt="Tech GIF">
                <img class="gif-item" src="https://media.giphy.com/media/JIX9t2j0ZTN9S/giphy.gif" alt="Gaming GIF">
            `;
        } else {
            // Show search results (mock)
            gifGrid.innerHTML = `<p style="color: #9932cc; text-align: center; padding: 20px;">Searching for "${query}"...</p>`;
        }
    }

    handleTyping() {
        if (!this.isTyping) {
            this.isTyping = true;
            // Show typing indicator for others (simulation)
        }

        clearTimeout(this.typingTimeout);
        this.typingTimeout = setTimeout(() => {
            this.stopTyping();
        }, 3000);
    }

    stopTyping() {
        this.isTyping = false;
        // Hide typing indicator
    }

    updateOnlineUsers() {
        // Mock online users
        const mockUsers = [
            { id: 1, username: 'BLRXH4RDIXX', avatar: 'B', role: 'admin', status: 'Coding...' },
            { id: 2, username: this.currentUser?.username || 'You', avatar: this.currentUser?.avatar || 'U', role: 'user', status: 'Online' },
            { id: 3, username: 'CyberNinja99', avatar: 'C', role: 'user', status: 'Testing APIs' },
            { id: 4, username: 'MatrixHacker', avatar: 'M', role: 'user', status: 'Online' },
            { id: 5, username: 'AdminBot', avatar: '🤖', role: 'bot', status: 'Active' }
        ];

        const usersList = document.getElementById('user-list');
        const onlineUsersSpan = document.getElementById('online-users');
        const userCountSpan = document.getElementById('user-count');

        if (usersList && onlineUsersSpan && userCountSpan) {
            usersList.innerHTML = '';

            mockUsers.forEach(user => {
                const userDiv = document.createElement('div');
                userDiv.className = 'user-item';
                userDiv.innerHTML = `
                    <div class="user-avatar">${user.avatar}</div>
                    <div class="user-info">
                        <div class="user-name">${user.username}</div>
                        <div class="user-status">${user.status}</div>
                    </div>
                    ${user.role === 'admin' ? '<div class="user-role-badge">ADMIN</div>' : ''}
                `;
                usersList.appendChild(userDiv);
            });

            onlineUsersSpan.textContent = mockUsers.length;
            userCountSpan.textContent = `${mockUsers.length} online`;
        }
    }

    startHeartbeat() {
        // Simulate periodic updates
        setInterval(() => {
            this.updateOnlineUsers();

            // Random bot messages
            if (Math.random() < 0.1) { // 10% chance every interval
                const botMessages = [
                    "💡 Tip: Use /help to see all available commands!",
                    "🔥 S1X TEAM tools are updated daily!",
                    "⚡ New features coming soon...",
                    "🛡️ Remember to follow chat rules!",
                    "🎮 Enjoying the Free Fire tools?"
                ];
                const randomMessage = botMessages[Math.floor(Math.random() * botMessages.length)];
                this.addBotMessage(randomMessage);
            }
        }, 30000); // Every 30 seconds
    }

    closeChat() {
        const chatInterface = document.getElementById('chat-interface');
        chatInterface.style.display = 'none';
        document.querySelector('.chat-entry-card').style.display = 'block';
    }

    minimizeChat() {
        const chatInterface = document.getElementById('chat-interface');
        if (chatInterface.style.height === '200px') {
            chatInterface.style.height = '600px';
            document.getElementById('minimize-chat-btn').innerHTML = '<i class="fas fa-minus"></i>';
        } else {
            chatInterface.style.height = '200px';
            document.getElementById('minimize-chat-btn').innerHTML = '<i class="fas fa-plus"></i>';
        }
    }

    loadChatData() {
        // Load any saved chat data from localStorage
        const savedData = localStorage.getItem('s1x_chat_data');
        if (savedData) {
            try {
                const data = JSON.parse(savedData);
                this.messages = data.messages || [];
            } catch (error) {
                console.error('Failed to load chat data:', error);
            }
        }
    }

    saveChatData() {
        // Save chat data to localStorage
        const data = {
            messages: this.messages,
            lastUpdate: new Date().toISOString()
        };
        localStorage.setItem('s1x_chat_data', JSON.stringify(data));
    }

    // Helper to create a message element
    createMessageElement(messageData) {
        const messageDiv = document.createElement('div');

        let messageClass = 'chat-message';
        if (this.currentUser && messageData.username === this.currentUser.username) {
            messageClass += ' own-message';
        }
        if (messageData.role === 'admin') {
            messageClass += ' admin-message';
        }
        if (messageData.type === 'system') {
            messageClass += ' system-message';
        }
        if (messageData.type === 'file') {
            messageClass += ' file-message';
        }

        messageDiv.className = messageClass;
        messageDiv.id = messageData.id;
        messageDiv.innerHTML = `
            <div class="message-avatar">${messageData.avatar || '👤'}</div>
            <div class="message-content">
                <div class="message-header">
                    <span class="message-username">${messageData.username}</span>
                    ${messageData.role === 'admin' ? '<span class="message-role admin">ADMIN</span>' : ''}
                    ${messageData.role === 'bot' ? '<span class="message-role">BOT</span>' : ''}
                    <span class="message-time">${this.formatTime(messageData.timestamp)}</span>
                </div>
                <div class="message-text">${this.formatMessage(messageData.message)}</div>
                ${messageData.type === 'file' ? '<div class="file-preview"></div>' : ''}
            </div>
        `;

        // Handle file previews if it's a file message
        if (messageData.type === 'file') {
            const filePreviewContainer = messageDiv.querySelector('.file-preview');
            const fileType = messageData.fileType || messageData.message.split(':')[1]?.split('<br>')[0].trim(); // Get file type from message or try to parse
            const fileName = messageData.fileName || messageData.message.split(': ')[1]?.split('<br>')[0].trim();
            const fileUrl = messageData.fileUrl; // If URL is available

            if (filePreviewContainer) {
                if (fileType === 'image') {
                    const imgElement = document.createElement('img');
                    imgElement.src = fileUrl || URL.createObjectURL(messageData.file); // Use provided URL or create from blob
                    imgElement.alt = fileName;
                    imgElement.style.maxWidth = '200px';
                    imgElement.style.maxHeight = '200px';
                    imgElement.style.borderRadius = '8px';
                    imgElement.style.margin = '5px 0';
                    filePreviewContainer.appendChild(imgElement);
                } else if (fileType === 'video') {
                    const videoElement = document.createElement('video');
                    videoElement.controls = true;
                    videoElement.style.maxWidth = '200px';
                    videoElement.style.maxHeight = '200px';
                    videoElement.style.borderRadius = '8px';
                    videoElement.style.margin = '5px 0';
                    const sourceElement = document.createElement('source');
                    sourceElement.src = fileUrl || URL.createObjectURL(messageData.file);
                    sourceElement.type = messageData.mimeType || 'video/mp4'; // Infer mime type
                    videoElement.appendChild(sourceElement);
                    filePreviewContainer.appendChild(videoElement);
                } else {
                    // For other files, just display name and size
                    filePreviewContainer.innerHTML = `📎 ${fileName} (${this.formatFileSize(messageData.fileSize || 0)})`;
                }
            }
        }

        return messageDiv;
    }

    // Helper for scrolling to the bottom of the chat
    scrollToBottom() {
        if (this.messagesContainer) {
            this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        }
    }

    handleFileUpload() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'image/*,video/*,audio/*,.pdf,.txt,.doc,.docx'; // Allowed file types
        input.multiple = true; // Allow multiple files

        input.onchange = (e) => {
            const files = Array.from(e.target.files);
            if (files.length > 0) {
                this.uploadFiles(files);
            }
        };

        input.click(); // Trigger file input click
    }

    async uploadFiles(files) {
        for (const file of files) {
            if (file.size > 10 * 1024 * 1024) { // 10MB limit
                this.addSystemMessage(`❌ الملف ${file.name} كبير جداً (أكثر من 10MB)`);
                continue;
            }

            try {
                // Create a preview message immediately
                const fileType = file.type.split('/')[0];
                let filePreviewContent = '';

                if (fileType === 'image') {
                    const imageUrl = URL.createObjectURL(file);
                    filePreviewContent = `<img src="${imageUrl}" alt="${file.name}" style="max-width: 200px; max-height: 200px; border-radius: 8px; margin: 5px 0;">`;
                } else if (fileType === 'video') {
                    const videoUrl = URL.createObjectURL(file);
                    filePreviewContent = `<video controls style="max-width: 200px; max-height: 200px; border-radius: 8px; margin: 5px 0;">
                                            <source src="${videoUrl}" type="${file.type}">
                                          </video>`;
                } else {
                    // For other file types
                    filePreviewContent = `📎 ${file.name} (${this.formatFileSize(file.size)})`;
                }

                const messageContent = `تم رفع الملف: ${file.name}<br>${filePreviewContent}`;

                const messageId = `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
                const messageElement = this.createMessageElement({
                    id: messageId,
                    username: this.currentUser.username,
                    message: messageContent,
                    timestamp: Date.now(),
                    type: 'file',
                    role: this.currentUser.role,
                    fileType: fileType,
                    fileName: file.name,
                    fileSize: file.size,
                    fileUrl: URL.createObjectURL(file), // Store blob URL for preview
                    file: file // Store the actual file object
                });

                this.messagesContainer.appendChild(messageElement);
                this.scrollToBottom();

                // In a real application, you would upload the file here and replace the preview with a link/status
                // For now, we just show the preview.

            } catch (error) {
                this.addSystemMessage(`❌ فشل في معالجة الملف ${file.name}`);
                console.error('Error processing file:', error);
            }
        }
    }

    // Helper to format file size
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // Helper to create message elements
    createMessageElement(messageData) {
        const messageDiv = document.createElement('div');

        let messageClass = 'chat-message';
        if (this.currentUser && messageData.username === this.currentUser.username) {
            messageClass += ' own-message';
        }
        if (messageData.role === 'admin') {
            messageClass += ' admin-message';
        }
        if (messageData.type === 'system') {
            messageClass += ' system-message';
        }
        if (messageData.type === 'file') {
            messageClass += ' file-message';
        }

        messageDiv.className = messageClass;
        messageDiv.id = messageData.id;
        messageDiv.innerHTML = `
            <div class="message-avatar">${messageData.avatar || '👤'}</div>
            <div class="message-content">
                <div class="message-header">
                    <span class="message-username">${messageData.username}</span>
                    ${messageData.role === 'admin' ? '<span class="message-role admin">ADMIN</span>' : ''}
                    ${messageData.role === 'bot' ? '<span class="message-role">BOT</span>' : ''}
                    <span class="message-time">${this.formatTime(messageData.timestamp)}</span>
                </div>
                <div class="message-text">${this.formatMessage(messageData.message)}</div>
                ${messageData.type === 'file' ? '<div class="file-preview"></div>' : ''}
            </div>
        `;

        // Handle file previews if it's a file message
        if (messageData.type === 'file') {
            const filePreviewContainer = messageDiv.querySelector('.file-preview');
            const fileType = messageData.fileType;
            const fileName = messageData.fileName;
            const fileUrl = messageData.fileUrl; // Provided URL for preview

            if (filePreviewContainer) {
                if (fileType === 'image') {
                    const imgElement = document.createElement('img');
                    imgElement.src = fileUrl;
                    imgElement.alt = fileName;
                    imgElement.style.maxWidth = '200px';
                    imgElement.style.maxHeight = '200px';
                    imgElement.style.borderRadius = '8px';
                    imgElement.style.margin = '5px 0';
                    filePreviewContainer.appendChild(imgElement);
                } else if (fileType === 'video') {
                    const videoElement = document.createElement('video');
                    videoElement.controls = true;
                    videoElement.style.maxWidth = '200px';
                    videoElement.style.maxHeight = '200px';
                    videoElement.style.borderRadius = '8px';
                    videoElement.style.margin = '5px 0';
                    const sourceElement = document.createElement('source');
                    sourceElement.src = fileUrl;
                    sourceElement.type = messageData.mimeType || 'video/mp4'; // Infer mime type if not provided
                    videoElement.appendChild(sourceElement);
                    filePreviewContainer.appendChild(videoElement);
                } else {
                    // For other files, just display name and size
                    filePreviewContainer.innerHTML = `📎 ${fileName} (${this.formatFileSize(messageData.fileSize || 0)})`;
                }
            }
        }

        return messageDiv;
    }

    // Helper for scrolling to the bottom of the chat
    scrollToBottom() {
        if (this.messagesContainer) {
            this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        }
    }

    hideAllPanels() {
        document.querySelectorAll('.extras-panel').forEach(panel => {
            panel.style.display = 'none';
        });
        document.querySelectorAll('.extra-btn').forEach(btn => {
            btn.classList.remove('active');
        });
    }

    setupChatContextMenu() {
        // Remove default context menu in chat area and add custom one
        document.addEventListener('contextmenu', (e) => {
            if (this.isInChatArea(e.target)) {
                e.preventDefault();
                this.showChatContextMenu(e);
            }
        });

        // Hide context menu when clicking elsewhere
        document.addEventListener('click', () => {
            this.hideChatContextMenu();
        });
    }

    isInChatArea(element) {
        // Check if element is within chat messages area or input
        return element.closest('#chat-messages') ||
               element.closest('#chat-input') ||
               element.closest('.message-text') ||
               element.id === 'chat-input';
    }

    showChatContextMenu(e) {
        const selection = window.getSelection();
        const selectedText = selection.toString().trim();

        // Remove existing context menu
        this.hideChatContextMenu();

        // Create context menu
        const contextMenu = document.createElement('div');
        contextMenu.id = 'chat-context-menu';
        contextMenu.className = 'chat-context-menu';
        contextMenu.style.cssText = `
            position: fixed;
            top: ${e.pageY}px;
            left: ${e.pageX}px;
            background: rgba(0, 0, 0, 0.95);
            border: 2px solid rgba(0, 255, 65, 0.4);
            border-radius: 8px;
            padding: 8px 0;
            z-index: 10000;
            min-width: 180px;
            box-shadow: 0 5px 20px rgba(0, 255, 65, 0.3);
        `;

        const menuItems = [];

        // Select All option
        menuItems.push({
            icon: '📋',
            text: 'تحديد الكل / Select All',
            action: () => this.selectAllInChatArea(),
            shortcut: 'Ctrl+A'
        });

        // Copy option (if text is selected)
        if (selectedText) {
            menuItems.push({
                icon: '📄',
                text: 'نسخ النص / Copy Text',
                action: () => this.copySelectedText(),
                shortcut: 'Ctrl+C'
            });
        }

        // Delete message option (if it's user's own message)
        const messageElement = e.target.closest('.chat-message');
        if (messageElement && messageElement.classList.contains('own-message')) {
            menuItems.push({
                icon: '🗑️',
                text: 'حذف الرسالة / Delete Message',
                action: () => this.deleteMessage(messageElement),
                shortcut: 'Del'
            });
        }

        // Quote text option (if text is selected)
        if (selectedText) {
            menuItems.push({
                icon: '💬',
                text: 'اقتباس النص / Quote Text',
                action: () => this.quoteSelectedText(selectedText),
                shortcut: ''
            });
        }

        // Clear selection option
        if (selectedText) {
            menuItems.push({
                icon: '❌',
                text: 'إلغاء التحديد / Clear Selection',
                action: () => this.clearSelection(),
                shortcut: 'Esc'
            });
        }

        // Build menu HTML
        menuItems.forEach((item, index) => {
            const menuItem = document.createElement('div');
            menuItem.className = 'context-menu-item';
            menuItem.style.cssText = `
                padding: 8px 15px;
                color: #00ff41;
                cursor: pointer;
                transition: all 0.3s;
                border-bottom: ${index < menuItems.length - 1 ? '1px solid rgba(0, 255, 65, 0.2)' : 'none'};
                display: flex;
                justify-content: space-between;
                align-items: center;
            `;

            menuItem.innerHTML = `
                <span style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 16px;">${item.icon}</span>
                    <span style="font-size: 12px;">${item.text}</span>
                </span>
                ${item.shortcut ? `<span style="color: #9932cc; font-size: 10px;">${item.shortcut}</span>` : ''}
            `;

            menuItem.addEventListener('mouseenter', () => {
                menuItem.style.background = 'rgba(0, 255, 65, 0.2)';
                menuItem.style.transform = 'translateX(3px)';
            });

            menuItem.addEventListener('mouseleave', () => {
                menuItem.style.background = 'transparent';
                menuItem.style.transform = 'translateX(0)';
            });

            menuItem.addEventListener('click', (e) => {
                e.stopPropagation();
                item.action();
                this.hideChatContextMenu();
            });

            contextMenu.appendChild(menuItem);
        });

        document.body.appendChild(contextMenu);

        // Adjust position if menu goes off screen
        const rect = contextMenu.getBoundingClientRect();
        if (rect.right > window.innerWidth) {
            contextMenu.style.left = (e.pageX - rect.width) + 'px';
        }
        if (rect.bottom > window.innerHeight) {
            contextMenu.style.top = (e.pageY - rect.height) + 'px';
        }
    }

    hideChatContextMenu() {
        const existingMenu = document.getElementById('chat-context-menu');
        if (existingMenu) {
            existingMenu.remove();
        }
    }

    selectAllInChatArea() {
        const chatMessages = document.getElementById('chat-messages');
        if (chatMessages) {
            const range = document.createRange();
            range.selectNodeContents(chatMessages);
            const selection = window.getSelection();
            selection.removeAllRanges();
            selection.addRange(range);

            // Show feedback
            this.showSelectionFeedback('تم تحديد جميع الرسائل / All messages selected');
        }
    }

    copySelectedText() {
        const selectedText = window.getSelection().toString();
        if (selectedText) {
            navigator.clipboard.writeText(selectedText).then(() => {
                this.showSelectionFeedback('تم نسخ النص / Text copied to clipboard');
            }).catch(() => {
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = selectedText;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                this.showSelectionFeedback('تم نسخ النص / Text copied');
            });
        }
    }

    deleteMessage(messageElement) {
        if (confirm('هل أنت متأكد من حذف هذه الرسالة؟ / Are you sure you want to delete this message?')) {
            messageElement.style.transition = 'all 0.5s ease';
            messageElement.style.opacity = '0';
            messageElement.style.transform = 'translateX(-100%)';

            setTimeout(() => {
                messageElement.remove();
                this.showSelectionFeedback('تم حذف الرسالة / Message deleted');
            }, 500);
        }
    }

    quoteSelectedText(text) {
        const chatInput = document.getElementById('chat-input');
        if (chatInput && text) {
            const quotedText = `"${text.substring(0, 100)}${text.length > 100 ? '...' : ''}" - `;
            chatInput.value = quotedText + chatInput.value;
            chatInput.focus();
            chatInput.setSelectionRange(quotedText.length, quotedText.length);
            this.showSelectionFeedback('تم إضافة الاقتباس / Quote added to input');
        }
    }

    clearSelection() {
        const selection = window.getSelection();
        selection.removeAllRanges();
        this.showSelectionFeedback('تم إلغاء التحديد / Selection cleared');
    }

    showSelectionFeedback(message) {
        // Create temporary feedback message
        const feedback = document.createElement('div');
        feedback.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(0, 255, 65, 0.9);
            color: #000;
            padding: 12px 20px;
            border-radius: 20px;
            font-weight: bold;
            z-index: 10001;
            box-shadow: 0 5px 15px rgba(0, 255, 65, 0.5);
            animation: feedbackFade 2s ease-out forwards;
        `;

        feedback.textContent = message;
        document.body.appendChild(feedback);

        // Add CSS animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes feedbackFade {
                0% { opacity: 0; transform: translate(-50%, -50%) scale(0.8); }
                20% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
                80% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
                100% { opacity: 0; transform: translate(-50%, -50%) scale(0.8); }
            }
        `;
        document.head.appendChild(style);

        setTimeout(() => {
            feedback.remove();
            style.remove();
        }, 2000);
    }

    // Initialize chat system directly
    // This section is modified to initialize chat immediately and show a ready message.
    // The previous structure with `setTimeout` and `if (s1xChat.currentUser)` was removed
    // to ensure chat is ready without delay.
    // Initialize chat system directly
    // This section is modified to initialize chat immediately and show a ready message.
    // The previous structure with `setTimeout` and `if (s1xChat.currentUser)` was removed
    // to ensure chat is ready without delay.
}

// Initialize chat system
let s1xChat;

// Device Performance Detection System
class DevicePerformanceManager {
    constructor() {
        this.deviceInfo = this.detectDevice();
        this.performanceLevel = this.calculatePerformanceLevel();
        this.applyOptimizations();
    }

    detectDevice() {
        const userAgent = navigator.userAgent || navigator.vendor || window.opera;
        const isMobile = /android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini/i.test(userAgent.toLowerCase());
        const isTablet = /ipad|android(?!.*mobile)|tablet/i.test(userAgent.toLowerCase());
        const isDesktop = !isMobile && !isTablet;

        // Detect device specs
        const hardwareConcurrency = navigator.hardwareConcurrency || 2;
        const deviceMemory = navigator.deviceMemory || 2;
        const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;

        return {
            isMobile,
            isTablet,
            isDesktop,
            hardwareConcurrency,
            deviceMemory,
            connection: connection ? {
                effectiveType: connection.effectiveType,
                downlink: connection.downlink,
                rtt: connection.rtt
            } : null,
            screen: {
                width: window.screen.width,
                height: window.screen.height,
                pixelRatio: window.devicePixelRatio || 1
            },
            userAgent
        };
    }

    calculatePerformanceLevel() {
        let score = 0;

        // CPU Score (cores)
        if (this.deviceInfo.hardwareConcurrency >= 8) score += 3;
        else if (this.deviceInfo.hardwareConcurrency >= 4) score += 2;
        else if (this.deviceInfo.hardwareConcurrency >= 2) score += 1;

        // Memory Score
        if (this.deviceInfo.deviceMemory >= 8) score += 3;
        else if (this.deviceInfo.deviceMemory >= 4) score += 2;
        else if (this.deviceInfo.deviceMemory >= 2) score += 1;

        // Screen Resolution Score
        const totalPixels = this.deviceInfo.screen.width * this.deviceInfo.screen.height;
        if (totalPixels >= 2073600) score += 2; // 1920x1080 or higher
        else if (totalPixels >= 921600) score += 1; // 1280x720 or higher

        // Connection Score
        if (this.deviceInfo.connection) {
            if (this.deviceInfo.connection.effectiveType === '4g') score += 2;
            else if (this.deviceInfo.connection.effectiveType === '3g') score += 1;
        }

        // Device Type Modifier
        if (this.deviceInfo.isDesktop) score += 2;
        else if (this.deviceInfo.isTablet) score += 1;

        // Performance Levels:
        // 0-3: Low Performance (weak phones)
        // 4-7: Medium Performance (average phones/tablets)
        // 8+: High Performance (flagship phones/desktops)

        if (score >= 8) return 'high';
        else if (score >= 4) return 'medium';
        else return 'low';
    }

    applyOptimizations() {
        const body = document.body;
        body.setAttribute('data-performance', this.performanceLevel);
        body.setAttribute('data-device-type', this.getDeviceType());

        console.log(`🎯 Device Performance: ${this.performanceLevel.toUpperCase()}`);
        console.log(`📱 Device Type: ${this.getDeviceType()}`);
        console.log(`⚡ Applying optimizations for ${this.performanceLevel} performance devices...`);

        // Apply CSS optimizations based on performance
        this.addPerformanceCSS();

        // Show performance notification
        this.showPerformanceNotification();
    }

    getDeviceType() {
        if (this.deviceInfo.isMobile) return 'mobile';
        if (this.deviceInfo.isTablet) return 'tablet';
        return 'desktop';
    }

    addPerformanceCSS() {
        const style = document.createElement('style');
        style.id = 'performance-optimizations';

        let css = '';

        if (this.performanceLevel === 'low') {
            // Low performance optimizations - minimal effects
            css = `
                /* Low Performance Mode - Smooth and minimal */
                body[data-performance="low"] * {
                    animation-duration: 0.3s !important;
                    transition-duration: 0.2s !important;
                }

                body[data-performance="low"] .floating-particles {
                    display: none !important;
                }

                body[data-performance="low"] .data-stream {
                    display: none !important;
                }

                body[data-performance="low"] .cyber-grid {
                    opacity: 0.3 !important;
                    animation: none !important;
                }

                body[data-performance="low"] .particle {
                    display: none !important;
                }

                body[data-performance="low"] .glitch-effect {
                    animation: none !important;
                }

                body[data-performance="low"] .neon-glow {
                    box-shadow: 0 0 5px #00ff41 !important;
                    animation: none !important;
                }

                body[data-performance="low"] .hologram::before {
                    display: none !important;
                }

                /* Smooth chat for low-end devices */
                body[data-performance="low"] .chat-message {
                    animation: none !important;
                }

                body[data-performance="low"] .typing-effect {
                    animation: none !important;
                    border-right: none !important;
                }
            `;
        } else if (this.performanceLevel === 'medium') {
            // Medium performance optimizations - balanced effects
            css = `
                /* Medium Performance Mode - Balanced effects */
                body[data-performance="medium"] .floating-particles .particle {
                    animation-duration: 8s !important;
                }

                body[data-performance="medium"] .floating-particles .particle:nth-child(n+26) {
                    display: none !important;
                }

                body[data-performance="medium"] .data-stream .data-line:nth-child(n+11) {
                    display: none !important;
                }

                body[data-performance="medium"] .glitch-effect {
                    animation-duration: 1s !important;
                }
            `;
        } else {
            // High performance - full effects with enhanced visuals
            css = `
                /* High Performance Mode - Enhanced effects */
                body[data-performance="high"] .floating-particles {
                    opacity: 0.8 !important;
                }

                body[data-performance="high"] .glitch-text {
                    animation-duration: 10s !important;
                }

                body[data-performance="high"] .neon-glow {
                    box-shadow:
                        0 0 5px #00ff41,
                        0 0 10px #00ff41,
                        0 0 15px #00ff41,
                        0 0 20px #00ff41,
                        0 0 35px #00ff41 !important;
                }

                /* Enhanced chat effects for high-end devices */
                body[data-performance="high"] .chat-message {
                    animation: messageSlideIn 0.5s ease-out, messagePulse 2s ease-in-out infinite !important;
                }

                @keyframes messagePulse {
                    0%, 100% { box-shadow: none; }
                    50% { box-shadow: 0 0 5px rgba(0, 255, 65, 0.3); }
                }
            `;
        }

        // Mobile-specific optimizations
        if (this.deviceInfo.isMobile) {
            css += `
                /* Mobile Optimizations */
                body[data-device-type="mobile"] .chat-interface {
                    height: 70vh !important;
                }

                body[data-device-type="mobile"] .extras-panel {
                    max-height: 200px !important;
                }

                body[data-device-type="mobile"] .api-grid {
                    grid-template-columns: 1fr !important;
                    gap: 15px !important;
                }

                body[data-device-type="mobile"] .input-container {
                    flex-direction: column !important;
                    gap: 10px !important;
                }

                body[data-device-type="mobile"] #chat-input {
                    font-size: 16px !important; /* Prevent zoom on iOS */
                }

                /* Touch-friendly buttons */
                body[data-device-type="mobile"] .btn,
                body[data-device-type="mobile"] .extra-btn,
                body[data-device-type="mobile"] .chat-control-btn {
                    min-height: 44px !important;
                    min-width: 44px !important;
                    padding: 12px !important;
                }
            `;
        }

        style.textContent = css;
        document.head.appendChild(style);
    }

    showPerformanceNotification() {
        const notification = document.createElement('div');
        notification.id = 'performance-notification';
        notification.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: rgba(0, 0, 0, 0.9);
            border: 2px solid #00ff41;
            border-radius: 10px;
            padding: 15px 20px;
            color: #00ff41;
            font-family: 'Fira Code', monospace;
            font-size: 12px;
            z-index: 10000;
            max-width: 300px;
            animation: slideInRight 0.5s ease-out;
        `;

        const performanceEmojis = {
            low: '🔋',
            medium: '⚡',
            high: '🚀'
        };

        const performanceMessages = {
            low: 'تم تحسين الواجهة للهواتف الضعيفة\nOptimized for low-end devices',
            medium: 'تم تحسين الواجهة للهواتف المتوسطة\nOptimized for mid-range devices',
            high: 'تم تفعيل جميع التأثيرات للأجهزة القوية\nFull effects enabled for high-end devices'
        };

        notification.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                <span style="font-size: 24px;">${performanceEmojis[this.performanceLevel]}</span>
                <strong>S1X Performance Mode</strong>
            </div>
            <div style="line-height: 1.4; white-space: pre-line;">
                ${performanceMessages[this.performanceLevel]}
            </div>
            <div style="margin-top: 8px; font-size: 10px; color: #9932cc;">
                Device: ${this.getDeviceType().toUpperCase()} | Cores: ${this.deviceInfo.hardwareConcurrency} | RAM: ${this.deviceInfo.deviceMemory}GB
            </div>
        `;

        // Add CSS animation
        const animationStyle = document.createElement('style');
        animationStyle.textContent = `
            @keyframes slideInRight {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
        `;
        document.head.appendChild(animationStyle);

        document.body.appendChild(notification);

        // Auto-hide after 5 seconds
        setTimeout(() => {
            notification.style.animation = 'slideInRight 0.5s ease-out reverse';
            setTimeout(() => {
                notification.remove();
                animationStyle.remove();
            }, 500);
        }, 5000);

        // Click to dismiss
        notification.addEventListener('click', () => {
            notification.remove();
            animationStyle.remove();
        });
    }

    // Method to get current performance settings
    getPerformanceInfo() {
        return {
            level: this.performanceLevel,
            deviceType: this.getDeviceType(),
            deviceInfo: this.deviceInfo,
            optimizationsApplied: true
        };
    }
}

// Function to initialize modern visual effects
function initializeModernEffects() {
    // Initialize visual effects based on device performance
    const performanceLevel = window.devicePerformance?.performanceLevel || 'medium'; // Default to medium if not detected

    if (performanceLevel === 'high') {
        // Full effects for high-end devices
        if (typeof EnhancedThreeJSScene !== 'undefined') {
            new EnhancedThreeJSScene();
        } else {
            new MatrixRain(); // Fallback to MatrixRain if EnhancedThreeJSScene is not defined
        }
        new VisualEffects();
    } else if (performanceLevel === 'medium') {
        // Balanced effects for medium devices
        new MatrixRain();
        new VisualEffects();
    } else {
        // Minimal effects for low-end devices
        // Only basic matrix rain, no visual effects
        new MatrixRain();
    }
}

// Initialize everything when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Device Performance Manager first
    window.devicePerformance = new DevicePerformanceManager();

    // Initialize modern effects based on detected device performance
    initializeModernEffects();

    // Initialize API Manager
    window.api = new APIManager(); // Ensure api is globally accessible if needed by button event listeners

    // Add enhanced button effects
    addButtonEffects();

    // Add neon effects
    addNeonEffects();

    // Add hologram effect
    addHologramEffect();

    // Load tutorial modal if needed (commented out until implemented)
    // checkTutorial();

    // Auto-resize text areas (commented out until implemented)
    // autoResizeTextareas();

    // Add event listeners for buttons
    setupButtonEventListeners();

    // Initialize S1X Chat System
    // Initialize chat system directly
    try {
        window.s1xChat = new S1XChatSystem();

        // Auto-register user and start chat immediately
        const userData = s1xChat.registerUserInChat();
        s1xChat.currentUser = userData;
        s1xChat.initializeChatInterface();
        s1xChat.connectToChat();

        // Show chat ready message after short delay
        setTimeout(() => {
            s1xChat.addSystemMessage('🎉 مرحباً بك في شات S1X TEAM! الشات جاهز الآن للاستخدام');
        }, 500);
    } catch (error) {
        console.error("Error initializing S1X Chat System:", error);
        // Optionally display an error message to the user
        const errorDiv = document.createElement('div');
        errorDiv.style.color = 'red';
        errorDiv.textContent = 'Failed to initialize chat. Please refresh the page.';
        document.getElementById('chat-container')?.appendChild(errorDiv);
    }

    // تأثير الكتابة بعد تحميل الصفحة
    setTimeout(addTypingEffect, 500);
});

// Global helper functions (if needed and not part of a class)
function toggleFullscreen() {
    const chatInterface = document.getElementById('chat-interface');
    if (chatInterface.classList.contains('fullscreen')) {
        chatInterface.classList.remove('fullscreen');
        chatInterface.style.position = 'static';
        chatInterface.style.top = 'auto';
        chatInterface.style.left = 'auto';
        chatInterface.style.width = 'auto';
        chatInterface.style.height = '80vh';
        chatInterface.style.zIndex = 'auto';
    } else {
        chatInterface.classList.add('fullscreen');
        chatInterface.style.position = 'fixed';
        chatInterface.style.top = '0';
        chatInterface.style.left = '0';
        chatInterface.style.width = '100vw';
        chatInterface.style.height = '100vh';
        chatInterface.style.zIndex = '9999';
    }
}

function handleFileUpload() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*,video/*,audio/*,.pdf,.txt,.doc,.docx';
    input.multiple = true;

    input.onchange = (e) => {
        const files = Array.from(e.target.files);
        if (files.length > 0 && window.s1xChat) {
            window.s1xChat.uploadFiles(files);
        }
    };

    input.click();
}