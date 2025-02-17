/**
 * Demonstrates research workflow through real browser interaction.
 * Uses WebdriverIO for reliable browser automation.
 */
import { remote } from 'webdriverio';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

class ResearchDemo {
    constructor() {
        this.url = 'http://localhost:7860';
        this.resultsDir = path.join(__dirname, '../demo_results');
        this.currentResultsDir = null;
    }

    async setup() {
        // Browser configuration
        const opts = {
            hostname: 'localhost',
            port: 4444,
            logLevel: 'info',
            capabilities: {
                browserName: 'chrome',
                'goog:chromeOptions': {
                    args: [
                        '--no-sandbox',
                        '--disable-gpu',
                        '--window-size=1920,1080'
                    ]
                }
            }
        };

        // Create results directory
        await fs.mkdir(this.resultsDir, { recursive: true });
        this.currentResultsDir = path.join(
            this.resultsDir,
            new Date().toISOString().replace(/[:.]/g, '-')
        );
        await fs.mkdir(this.currentResultsDir);

        // Launch browser
        this.browser = await remote(opts);
        
        // Set reasonable timeouts
        await this.browser.setTimeout({
            implicit: 5000,
            pageLoad: 10000,
            script: 5000
        });
    }

    async runDemo() {
        try {
            await this.setup();
            console.log('Starting research workflow demo...');

            // Step 1: Load interface
            await this.loadInterface();

            // Step 2: Create project
            await this.createProject();

            // Step 3: Configure LLM
            await this.configureLLM();

            // Step 4: Run initial research
            const results = await this.runInitialResearch();

            // Step 5: Run follow-up research
            const refinedResults = await this.runFollowupResearch();

            // Step 6: Export results
            await this.exportResults(results, refinedResults);

            console.log('Demo completed successfully!');

        } catch (error) {
            console.error('Demo failed:', error);
            // Save error screenshot
            await this.browser.saveScreenshot(
                path.join(this.currentResultsDir, 'error.png')
            );
            throw error;

        } finally {
            await this.cleanup();
        }
    }

    async loadInterface() {
        console.log('Loading NovaAegis interface...');
        await this.browser.url(this.url);
        
        // Wait for header
        const header = await this.browser.$('h1*=NovaAegis Research Assistant');
        await header.waitForDisplayed();
    }

    async createProject() {
        console.log('Creating research project...');

        // Go to Projects tab
        const projectsTab = await this.browser.$('button=Projects');
        await projectsTab.click();

        // Create group
        const newGroupBtn = await this.browser.$('button=New Group');
        await newGroupBtn.click();

        // Fill group details
        await this.browser.$('input[aria-label="Group Name"]')
            .setValue('LLM Research');
        await this.browser.$('textarea[aria-label="Description"]')
            .setValue('Research on LLM architectures and techniques');
        await this.browser.$('button=Create').click();

        // Create project
        const newProjectBtn = await this.browser.$('button=New Project');
        await newProjectBtn.click();

        // Fill project details
        await this.browser.$('input[aria-label="Project Name"]')
            .setValue('HF Papers Analysis');
        await this.browser.$('textarea[aria-label="Description"]')
            .setValue('Analysis of recent HuggingFace papers');
        await this.browser.$('text=LLM Research').click();
        await this.browser.$('button=Create').click();

        // Verify creation
        await this.browser.$('text=HF Papers Analysis')
            .waitForDisplayed();
    }

    async configureLLM() {
        console.log('Configuring LLM settings...');

        // Go to LLM Settings
        const settingsTab = await this.browser.$('button=LLM Settings');
        await settingsTab.click();

        // Configure model
        await this.browser.$('input[value="Local"]').click();
        await this.browser.$('select[aria-label="Local Model"]')
            .selectByVisibleText('llama2-7b');
        await this.browser.$('input[aria-label="Model Path"]')
            .setValue('models/llama2-7b');

        // Set parameters
        await this.browser.$('input[aria-label="Temperature"]')
            .setValue('0.7');
        await this.browser.$('input[aria-label="Max Tokens"]')
            .setValue('2000');

        // Save settings
        await this.browser.$('button=Save LLM Settings').click();
        await this.browser.$('text=Settings saved successfully')
            .waitForDisplayed();
    }

    async runInitialResearch() {
        console.log('Running initial research...');

        // Go to Research tab
        const researchTab = await this.browser.$('button=Research');
        await researchTab.click();

        // Enter research query
        const query = `
        Research recent HuggingFace papers about LLM architectures.
        Focus on:
        - Novel architecture approaches
        - Performance improvements
        - Training innovations
        Create a structured knowledge graph and provide insights.
        `;
        await this.browser.$('textarea[aria-label="Research Request"]')
            .setValue(query);

        // Configure research
        await this.browser.$('input[aria-label="Focus Level"]')
            .setValue('0.8');
        await this.browser.$('input[aria-label="Research Depth"]')
            .setValue('4');

        // Start research
        await this.browser.$('button=Begin Research').click();

        // Wait for completion
        await this.browser.$('#knowledge-graph svg')
            .waitForDisplayed({ timeout: 60000 });
        await this.browser.$('.results-container')
            .waitForDisplayed();

        // Capture results
        const results = {
            graphData: await this.captureGraphData(),
            insights: await this.browser.$('.results-container').getText(),
            timestamp: new Date().toISOString()
        };

        // Save screenshot
        await this.browser.saveScreenshot(
            path.join(this.currentResultsDir, 'initial_research.png')
        );

        return results;
    }

    async runFollowupResearch() {
        console.log('Running follow-up research...');

        // Enter follow-up query
        const query = `
        Based on the previous research, what are the most promising
        approaches for improving LLM training efficiency?
        Focus on practical implementations and benchmarks.
        `;
        await this.browser.$('textarea[aria-label="Research Request"]')
            .setValue(query);

        // Start research
        await this.browser.$('button=Begin Research').click();

        // Wait for completion
        await this.browser.$('#knowledge-graph svg')
            .waitForDisplayed({ timeout: 60000 });
        await this.browser.$('.results-container')
            .waitForDisplayed();

        // Capture results
        const results = {
            graphData: await this.captureGraphData(),
            insights: await this.browser.$('.results-container').getText(),
            timestamp: new Date().toISOString()
        };

        // Save screenshot
        await this.browser.saveScreenshot(
            path.join(this.currentResultsDir, 'followup_research.png')
        );

        return results;
    }

    async exportResults(initialResults, followupResults) {
        console.log('Exporting results...');

        // Save combined results
        const results = {
            initial_research: initialResults,
            followup_research: followupResults,
            metadata: {
                timestamp: new Date().toISOString(),
                project: 'HF Papers Analysis'
            }
        };

        await fs.writeFile(
            path.join(this.currentResultsDir, 'research_results.json'),
            JSON.stringify(results, null, 2)
        );

        // Export from UI
        await this.browser.$('button=Export').click();

        // Wait for download and move file
        const downloadPath = await this.browser.getDownloadPath();
        const exportedFile = path.join(downloadPath, 'exported_results.json');
        await fs.rename(
            exportedFile,
            path.join(this.currentResultsDir, 'exported_results.json')
        );
    }

    async captureGraphData() {
        return await this.browser.execute(() => {
            const graphElement = document.querySelector('#knowledge-graph');
            return {
                nodes: graphElement.__data__.nodes,
                edges: graphElement.__data__.edges
            };
        });
    }

    async cleanup() {
        if (this.browser) {
            await this.browser.deleteSession();
        }
    }
}

// Run demo
const demo = new ResearchDemo();
demo.runDemo().catch(console.error);