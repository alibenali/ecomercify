/**
 * @license Copyright (c) 2003-2025, CKSource Holding sp. z o.o. All rights reserved.
 * For licensing, see https://ckeditor.com/legal/ckeditor-oss-license
 */

CKEDITOR.editorConfig = function( config ) {
    // UI language (optional)
    // config.language = 'fr';

    // Theme color (optional)
    // config.uiColor = '#AADC6E';

    // Enable image2 + uploadimage
    config.extraPlugins = 'uploadimage,image2';

    // Standard upload URL (used in the image dialog upload tab)
    config.filebrowserUploadUrl = '/upload/';
    config.filebrowserUploadMethod = 'form';

    // Paste/drag&drop upload API (⚠️ required by your build)
    config.pasteUploadFileApi = '/upload-paste/';  // 👈 set to your backend endpoint
};

CKEDITOR.disableAutoInline = true; 
CKEDITOR.config.versionCheck = false;
