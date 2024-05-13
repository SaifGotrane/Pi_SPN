import { Component } from '@angular/core';

@Component({
  selector: 'app-tab2',
  templateUrl: 'tab2.page.html',
  styleUrls: ['tab2.page.scss']
})
export class Tab2Page {

  constructor() {}
  goBack() {
    window.location.href = 'http://localhost:4200/intro';  }

  ngOnInit() {
    this.readCSV();
  }

  // Fonction pour lire le fichier CSV
  readCSV() {
    fetch('/assets/data.csv') // Chemin relatif vers le fichier CSV dans votre projet Angular
      .then(response => response.text())
      .then(csvData => {
        this.displayCSVData(csvData);
      })
      .catch(error => console.error('Error reading CSV file:', error));
  }

  // Fonction pour afficher les données CSV dans le tableau
  displayCSVData(csvData) {
    const rows = csvData.trim().split('\n');
    const table = document.getElementById('csv-table');

    rows.forEach((row, rowIndex) => {
      const columns = row.split(',');
      const tr = document.createElement('tr');

      columns.forEach((column, columnIndex) => {
        const cell = rowIndex === 0 ? 'th' : 'td'; // Utiliser th pour l'en-tête de colonne
        const td = document.createElement(cell);
        td.textContent = column.trim();
        tr.appendChild(td);
      });

      table.appendChild(tr);
    });
  }
}
