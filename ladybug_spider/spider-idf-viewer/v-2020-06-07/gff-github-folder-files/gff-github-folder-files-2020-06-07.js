/* globals GFFdivFileInfo, GFFdivGithubFoldersFiles */
/* jshint esversion: 6 */
/* jshint loopfunc: true */


const GFF = {
	extension: ".xml"
};

GFF.items = [
	{
		"user": "GreenBuildingXML",
		"repo": "/Sample-gbXML-Files",
		"pathRepo": "",
		"title": "gbXML.org sample files",
		"subTitle":
			`Files from the
		<a href="https://github.com/GreenBuildingXML/Sample_gbXML_Files" target="_blank">gbXML.org Sample Files</a>
		repository on GitHub.
		Includes a variety of gbXML files from various vendors and organizations.`
	},
	{
		"user": "ladybug-tools",
		"repo": "/spider",
		"pathRepo": "gbxml-sample-files/",
		"title": "Spider gbXML files",
		"subTitle":
			`Ladybug Tools / Spider
		<a href = "https://www.ladybug.tools/spider/#gbxml-sample-files/" target = "_blank" >sample files</a >
		on GitHub from a variety of sources`
	},
	{
		"user": "ladybug-tools",
		"repo": "/spider",
		"pathRepo": "gbxml-sample-files/samples-2/",
		"title": "Spider gbXML files #2",
		"subTitle":
			`Ladybug Tools / Spider gbXML Viewer
			<a href = "https://www.ladybug.tools/spider/#gbxml-sample-files-2/" target = "_blank" >sample files #2</a >
			on GitHub from a variety of sources`
	},
	{
		"user": "ladybug-tools",
		"repo": "/spider",
		"pathRepo": "cookbook/07-create-exportable-buildings/test-gbxml-files/",
		"title": "Build Well",
		"subTitle":
			`Parametrically created gbXML files from the Spider
		<a href="https://www.ladybug.tools/spider/#build-well/README.md" target="_blank">Build Well</a>
		 contributions to the
		<a href="https://speedwiki.io/" target="_blank">Perkins and Will SPEED</a>
	 	project`
	},
	{
		"user": "ladybug-tools",
		"repo": "/spider",
		"pathRepo": "gbxml-sample-files/zip/",
		"title": "Spider gbXML ZIP files",
		"subTitle":
			`Ladybug Tools / Spider gbXML
		<a href="https://www.ladybug.tools/spider/#gbxml-sample-files/README.md" target="_blank">sample gbXML data in ZIP files</a>
	 	on GitHub from a variety of sources`
	}
];


GFF.iconGitHubMark = "https://ladybug.tools/spider-2020/assets/icons/mark-github.svg";
GFF.iconInfo = `<img src=${GFF.iconGitHubMark} height=11 style=opacity:0.5 >`;

GFF.getMenuGithubFoldersFiles = function () {

	const htm = GFF.items.map( ( item, index ) =>
		`
		<details ontoggle="GFFdivFoldersFiles${ index}.innerHTML=GFF.getGithubFoldersFiles(${index});" >

			<summary id=TMPsumSurfaces >${ index + 1} - ${item.title}</summary>

			<div id=GFFdivFoldersFiles${ index} ></div>

		</details>
	`
	).join( "" );

	return htm;

};


GFF.getGithubFoldersFiles = function ( index ) {

	const item = GFF.items[ index ];

	item.urlGitHubApiContents = 'https://api.github.com/repos/' + item.user + item.repo + '/contents/' + item.pathRepo;

	GFF.index = index;

	const htm =
		`
		<p><i>${ item.subTitle}</i></p>

		<div id=GALdivGallery${ index} ></div>

		<p>Click any ${ GFF.iconInfo} icon to view file source code on GitHub.</p>

		<p>Click any file title to view the file in this script.</p>

		<p>Click any ❐ icon to go full screen & get link to individual file.</p>

		<p>Tool tips provide file size.

		<hr>

	`;

	GFF.requestFile( item.urlGitHubApiContents, GFF.callbackGitHubMenu, index );

	return htm;

};



GFF.requestFile = function ( url, callback, index ) {

	GFF.index = index;

	const xhr = new XMLHttpRequest();
	xhr.crossOrigin = 'anonymous';
	xhr.open( 'GET', url, true );
	xhr.onerror = function ( xhr ) { console.log( 'error:', xhr ); };
	xhr.onprogress = onRequestFileProgress;
	xhr.onload = callback;
	xhr.send( null );


	function onRequestFileProgress ( xhr ) {

		let name = xhr.target.responseURL.split( '/' ).pop();

		const item = GFF.items[ GFF.index ];

		name = name ? item.user + '/' + name : `${item.user}  ${item.repo} `;

		GFFdivFileInfo.innerHTML =
			`
			Files from: ${ name}<br>
			Bytes loaded: ${ xhr.loaded.toLocaleString()}<br>
		`;

	}

};



GFF.callbackGitHubMenu = function ( xhr ) {

	const response = xhr.target.response;
	const files = JSON.parse( response );

	let htm = '';

	const item = GFF.items[ GFF.index ];
	//console.log( 'item', item );

	item.branch = item.branch || "master";

	item.urlGitHubSource = 'https://github.com/' + item.user + item.repo + '/blob/master/' + item.pathRepo;

	item.urlGitHubPage = 'https://cdn.jsdelivr.net/gh/' + item.user + item.repo + '@' + item.branch + '/' + item.pathRepo;

	item.threeViewer = "../../spider-gbxml-viewer/index.html";

	let count = 1;
	for ( let file of files ) {

		if ( file.name.toLowerCase().endsWith( GFF.extension ) === false &&
			file.name.toLowerCase().endsWith( '.zip' ) === false ) { continue; }

		const fileName = encodeURI( file.name );

		htm +=

			`<div style=margin:4px 0; >

			<a href=${ item.urlGitHubSource + fileName} title="Edit me" >${GFF.iconInfo}</a>

			${ count ++ } <a href=#${ item.urlGitHubPage + fileName} title="${file.size.toLocaleString()} bytes" >${file.name}</a>

			<a href=${ item.threeViewer }#${item.urlGitHubPage}${fileName} title="Link to just this file" target="_blank" >&#x2750;</a>

		</div>`;

	}

	const divGallery = GFFdivGithubFoldersFiles.querySelectorAll( "#GALdivGallery" + GFF.index )[ 0 ];
	//console.log( 'divGallery', divGallery );

	divGallery.innerHTML = htm;

};
