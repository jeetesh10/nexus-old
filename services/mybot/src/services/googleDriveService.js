/**
 * googleDriveService.js
 *
 * This module provides functions for interacting with the Google Drive API,
 * allowing the application to save and retrieve documents.
 */

const { google } = require('googleapis');
const path = require('path');
const fs = require('fs');

// IMPORTANT: You must set up a Google Service Account and download its JSON key file.
// Place the key file in your project and update the path below.
const GOOGLE_API_KEY_PATH = path.join(__dirname, '..', '..', 'credentials', 'google-service-account.json');
// The ID of the parent folder where all your project folders will be created.
const GOOGLE_DRIVE_PARENT_FOLDER_ID = '1ZSWqrDKLnpSEJA1JeIgScDytzEMYz6Aw';

// Authenticate with Google Drive API using a service account
const auth = new google.auth.GoogleAuth({
    keyFile: GOOGLE_API_KEY_PATH,
    scopes: ['https://www.googleapis.com/auth/drive.file']
});

const drive = google.drive({ version: 'v3', auth });

/**
 * Uploads a document to the designated Google Drive folder.
 * @param {string} projectName - The name of the project to use as a folder name.
 * @param {string} fileName - The name of the file to be saved.
 * @param {string} content - The content of the document.
 * @returns {Promise<string>} The ID of the created file.
 */
async function uploadDocument(projectName, fileName, content) {
    try {
        const folderId = await findOrCreateFolder(projectName);

        const fileMetadata = {
            name: fileName,
            parents: [folderId]
        };

        const media = {
            mimeType: 'text/plain',
            body: content
        };

        const file = await drive.files.create({
            resource: fileMetadata,
            media: media,
            fields: 'id'
        });

        console.log(`File '${fileName}' uploaded to folder '${projectName}'. File ID: ${file.data.id}`);
        return file.data.id;
    } catch (err) {
        console.error('Error uploading file to Google Drive:', err);
        throw new Error('Failed to upload document to Google Drive.');
    }
}

/**
 * Finds a folder by name or creates it if it doesn't exist.
 * @param {string} folderName - The name of the folder to find or create.
 * @returns {Promise<string>} The ID of the folder.
 */
async function findOrCreateFolder(folderName) {
    const searchResponse = await drive.files.list({
        q: `name='${folderName}' and mimeType='application/vnd.google-apps.folder' and '${GOOGLE_DRIVE_PARENT_FOLDER_ID}' in parents`,
        fields: 'files(id)'
    });

    if (searchResponse.data.files.length > 0) {
        return searchResponse.data.files[0].id;
    }

    const fileMetadata = {
        name: folderName,
        mimeType: 'application/vnd.google-apps.folder',
        parents: [GOOGLE_DRIVE_PARENT_FOLDER_ID]
    };

    const folder = await drive.files.create({
        resource: fileMetadata,
        fields: 'id'
    });

    console.log(`Created new folder: '${folderName}' with ID: ${folder.data.id}`);
    return folder.data.id;
}

/**
 * Retrieves the content of a document from Google Drive.
 * @param {string} fileId - The ID of the file to retrieve.
 * @returns {Promise<string>} The content of the file.
 */
async function getDocument(fileId) {
    try {
        const response = await drive.files.get({
            fileId: fileId,
            alt: 'media'
        });

        return response.data;
    } catch (err) {
        console.error('Error retrieving file from Google Drive:', err);
        throw new Error('Failed to retrieve document from Google Drive.');
    }
}

module.exports = {
    uploadDocument,
    getDocument
};