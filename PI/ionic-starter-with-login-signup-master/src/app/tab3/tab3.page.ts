import { Component } from '@angular/core';
import { ModelService } from '../model.service';
import { saveAs } from 'file-saver';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-tab3',
  templateUrl: 'tab3.page.html',
  styleUrls: ['tab3.page.scss']
})
export class Tab3Page {
  formData: any = {};
  typeClient: string;
  clusterLabel: string;
  nawnaw:string;
  constructor(private modelService: ModelService, private http: HttpClient) { }

  submitForm(formData: any): void {
    const { clientName, spn, numberOfCars, numberOfRequests, clientId } = formData;

    // Prepare the data for clustering
    const data = {
      SPN: spn,
      'Number of cars': numberOfCars,
      'nombre de request': numberOfRequests
    };

    // Send the data to your backend API for clustering
    this.http.post<any>('http://localhost:5000/api/clustering', data)
    .subscribe(
      (response) => {
        // Handle the clustering prediction response here
        console.log('Clustering prediction:', response);
        // Determine nawnaw based on the response value
        if (response === 0) {
          this.nawnaw = 'This new client is renting for the first time and may be categorized as a bronze client.';
        } else if (response === 1) {
          this.nawnaw = 'This new client is renting for the first time and may be categorized as a golden client.';
        } else {
          this.nawnaw = 'This new client is considered a normal client; their status may change based on future rentals.';
        }
      },
      (error) => {
        // Handle errors here
        console.error('Error submitting form:', error);
      }
    );

  }
  submitnounou(): void {
    const { columnName } = this.formData;

    // Call parseCSV function with the provided column name
    this.parseCSV(columnName);
  }

  parseCSV(columnName: string): void {
    // Parse CSV and find the corresponding value
    this.http.get('assets/Tab3/clustered_data.csv', { responseType: 'text' })
      .subscribe(
        (data) => {
          // Split CSV data into rows
          var rows = data.split('\n');
          
          // Loop through rows to find matching column name
          var found = false;
          var clusterLabel;
          for (var i = 0; i < rows.length; i++) {
            var columns = rows[i].split(',');
            if (columns[0] === columnName) { // Assuming the first column contains the column names
              clusterLabel = columns[5]; // Assuming the second column contains the Cluster Labels
              found = true;
              console.log('type client', clusterLabel);
              break;
            }
          }
          
          // Display result
          if (!found) {
            this.typeClient = "This client is a new client";
          }

          // Set typeClient based on clusterLabel value
          switch (clusterLabel) {
            case '0':
              this.typeClient = 'This client is considered as a bronze client';
              break;
            case '1':
              this.typeClient = 'This client is considered as a golden client';
              break;
            case '2':
              this.typeClient = 'This client is considered as a normal client';
              break;
          }
          console.log('type client', this.typeClient);
        },
        (error) => {
          console.error('Error fetching CSV:', error);
        }
      );
  }
}