package mobile.common;

import java.util.ArrayList;
import java.util.List;

/**
 * Manager for handling large language models within the mobile app.
 */
public class LLMManager {

    private List<String> downloadedModels;

    public LLMManager() {
        downloadedModels = new ArrayList<>();
    }

    /**
     * Downloads a large language model.
     * @param modelName The name of the model to download.
     */
    public void downloadModel(String modelName) {
        // Placeholder for download logic
        downloadedModels.add(modelName);
    }

    /**
     * Runs a large language model.
     * @param modelName The name of the model to run.
     */
    public void runModel(String modelName) {
        // Placeholder for run logic
    }

    /**
     * Retrieves all downloaded models.
     * @return A list of downloaded model names.
     */
    public List<String> getDownloadedModels() {
        return downloadedModels;
    }
}
