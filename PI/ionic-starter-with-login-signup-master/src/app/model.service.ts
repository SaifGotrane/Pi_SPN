import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { catchError, tap } from 'rxjs/operators';
import { of } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ModelService {

  constructor(private http: HttpClient) { }

  getClusteringResults() {
    console.log("Sending GET request to server for clustering results...");
    return this.http.get<any[]>('http://localhost:5000/get_model').pipe(
      tap(results => {
        console.log("Clustering results received from server:", results);
      }),
      catchError(error => {
        console.error("Error occurred while fetching clustering results:", error);
        return of([]);
      })
    );
  }
}