(function(global) {

	// map tells the System loader where to look for things
	var map = {
		'login': 'client/modules/login',
		'main': 'client/modules/main',
		'modules': 'client/modules', // 'dist',
		'components': 'client/components',
		'services': 'client/services',
		'rxjs': 'client/node_modules/rxjs',
		//'angular2-in-memory-web-api': 'client/node_modules/angular2-in-memory-web-api',
		'@angular': 'client/node_modules/@angular',
		'ts': 'client/node_modules/plugin-typescript/lib/plugin.js',
		'tsconfig.json': 'client/tsconfig.json',
		'typescript': 'client/node_modules/typescript/lib/typescript.js',
	};

	// packages tells the System loader how to load when no filename and/or no extension
	var packages = {
		'login': { main: 'login',  defaultExtension: 'ts' },
		'main': { main: 'main',  defaultExtension: 'ts' },
		'modules': { defaultExtension: 'ts' },
		'components': { defaultExtension: 'ts' },
		'services': { defaultExtension: 'ts' },
		'rxjs': { defaultExtension: 'js' },
		//'typescript': { defaultExtension: 'js' },
		//'angular2-in-memory-web-api': { defaultExtension: 'js' },
	};

	var ngPackageNames = [
		'common',
		'compiler',
		'core',
		'forms',
		'http',
		'platform-browser',
		'platform-browser-dynamic',
		'router',
		'router-deprecated',
		'testing',
		'upgrade',
	];

	// add package entries for angular packages in the form '@angular/common': { main: 'index.js', defaultExtension: 'js' }
	ngPackageNames.forEach(function(pkgName) {
		packages["@angular/" + pkgName] = {
			main: 'bundles/' + pkgName + '.umd.min.js', 
			//defaultExtension: 'js'
		};
	});

	var config = {
		map: map,
		packages: packages,
		transpiler: 'ts',
		typescriptOptions: { 
			tsconfig: true
		},
		meta: {
			typescript: {
				exports: "ts"
			}
		}
	};

	// filterSystemConfig - index.html's chance to modify config before we register it.
	if (global.filterSystemConfig) { global.filterSystemConfig(config); }

	SystemJS.config(config);
})(this);